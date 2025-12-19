# TaskGroup Migration Example

**Concrete example of migrating from `asyncio.gather()` to `asyncio.TaskGroup`**

---

## Current Implementation

```python
# tapps_agents/workflow/parallel_executor.py:323-324
tasks = [execute_with_retries(step) for step in steps]
task_results = await asyncio.gather(*tasks, return_exceptions=True)
```

## Improved Implementation with TaskGroup

```python
async def execute_parallel(
    self,
    steps: list[WorkflowStep],
    execute_fn: Callable[[WorkflowStep], Any],
    *,
    state: WorkflowState,
    timeout_seconds: float | None = None,
) -> list[StepExecutionResult]:
    """
    Execute multiple steps in parallel with structured concurrency.
    
    Uses asyncio.TaskGroup (Python 3.11+) for automatic cancellation
    propagation and better error handling.
    """
    if not steps:
        return []
    
    timeout = timeout_seconds or self.default_timeout_seconds
    semaphore = asyncio.Semaphore(self.max_parallel)
    
    results: list[StepExecutionResult] = []
    
    # Use TaskGroup for structured concurrency
    # TaskGroup automatically cancels all tasks if any task raises an exception
    try:
        async with asyncio.TaskGroup() as tg:
            tasks: dict[asyncio.Task[StepExecutionResult], WorkflowStep] = {}
            
            for step in steps:
                task = tg.create_task(
                    self._execute_with_semaphore_and_retries(
                        step=step,
                        execute_fn=execute_fn,
                        semaphore=semaphore,
                        timeout=timeout,
                        state=state,
                    )
                )
                tasks[task] = step
        
        # All tasks completed successfully
        # Collect results
        for task, step in tasks.items():
            result = await task
            results.append(result)
    
    except* Exception as eg:
        # Handle ExceptionGroup (Python 3.11+)
        # This catches all exceptions from the TaskGroup
        logger.error(
            f"Parallel execution failed with {len(eg.exceptions)} exceptions",
            extra={
                "workflow_id": state.workflow_id,
                "exception_count": len(eg.exceptions),
            }
        )
        
        # Collect results from completed tasks
        for task, step in tasks.items():
            if task.done():
                try:
                    result = await task
                    results.append(result)
                except Exception as e:
                    # Task completed but raised exception
                    logger.error(f"Step {step.id} failed: {e}")
                    results.append(
                        self._create_failed_result(step, e, state)
                    )
            else:
                # Task was cancelled by TaskGroup
                logger.warning(f"Step {step.id} was cancelled")
                results.append(
                    self._create_cancelled_result(step, state)
                )
        
        # Re-raise the first exception for upstream handling
        if eg.exceptions:
            raise eg.exceptions[0]
    
    # Sort by step.id for deterministic ordering
    results.sort(key=lambda r: r.step.id)
    return results

async def _execute_with_semaphore_and_retries(
    self,
    step: WorkflowStep,
    execute_fn: Callable[[WorkflowStep], Any],
    semaphore: asyncio.Semaphore,
    timeout: float | None,
    state: WorkflowState,
) -> StepExecutionResult:
    """Execute step with semaphore, timeout, and retries."""
    retry_config = self._get_retry_config(step)
    step_execution = StepExecution(
        step_id=step.id,
        agent=step.agent or "",
        action=step.action or "",
        started_at=datetime.now(),
        status="running",
    )
    
    # Record start in state
    state.step_executions.append(step_execution)
    
    async with semaphore:
        last_error: Exception | None = None
        attempts = 0
        
        while attempts < retry_config.max_attempts:
            attempts += 1
            try:
                # Use asyncio.timeout for better cancellation support
                if timeout:
                    async with asyncio.timeout(timeout):
                        artifacts = await execute_fn(step)
                else:
                    artifacts = await execute_fn(step)
                
                # Success
                step_execution.completed_at = datetime.now()
                step_execution.duration_seconds = (
                    step_execution.completed_at - step_execution.started_at
                ).total_seconds()
                step_execution.status = "completed"
                
                return StepExecutionResult(
                    step=step,
                    step_execution=step_execution,
                    artifacts=artifacts,
                    attempts=attempts,
                )
            
            except TimeoutError as e:
                last_error = e
                step_execution.error = f"Step timed out after {timeout}s"
                
                if not retry_config.should_retry(attempts, e):
                    break
                
                backoff = retry_config.get_backoff_seconds(attempts)
                await asyncio.sleep(backoff)
                continue
            
            except asyncio.CancelledError:
                # Task was cancelled - don't retry
                step_execution.status = "cancelled"
                step_execution.error = "Step execution was cancelled"
                raise  # Re-raise to propagate cancellation
            
            except Exception as e:
                last_error = e
                step_execution.error = str(e)
                
                if not retry_config.should_retry(attempts, e):
                    break
                
                backoff = retry_config.get_backoff_seconds(attempts)
                await asyncio.sleep(backoff)
                continue
        
        # All retries exhausted
        step_execution.completed_at = datetime.now()
        step_execution.duration_seconds = (
            step_execution.completed_at - step_execution.started_at
        ).total_seconds()
        step_execution.status = "failed"
        
        return StepExecutionResult(
            step=step,
            step_execution=step_execution,
            error=last_error,
            attempts=attempts,
        )

def _create_failed_result(
    self,
    step: WorkflowStep,
    error: Exception,
    state: WorkflowState,
) -> StepExecutionResult:
    """Create a failed result for a step."""
    return StepExecutionResult(
        step=step,
        step_execution=StepExecution(
            step_id=step.id,
            agent=step.agent or "",
            action=step.action or "",
            started_at=datetime.now(),
            completed_at=datetime.now(),
            status="failed",
            error=str(error),
        ),
        error=error,
    )

def _create_cancelled_result(
    self,
    step: WorkflowStep,
    state: WorkflowState,
) -> StepExecutionResult:
    """Create a cancelled result for a step."""
    return StepExecutionResult(
        step=step,
        step_execution=StepExecution(
            step_id=step.id,
            agent=step.agent or "",
            action=step.action or "",
            started_at=datetime.now(),
            completed_at=datetime.now(),
            status="cancelled",
            error="Step execution was cancelled",
        ),
    )
```

## Key Improvements

1. **Automatic Cancellation**: TaskGroup automatically cancels all tasks if any task raises an exception
2. **Better Error Handling**: ExceptionGroup provides structured exception handling
3. **Resource Safety**: TaskGroup ensures all tasks complete before returning
4. **Cancellation Propagation**: Proper handling of `asyncio.CancelledError`
5. **Modern Python**: Uses Python 3.11+ features (`asyncio.TaskGroup`, `asyncio.timeout`, `except*`)

## Migration Checklist

- [ ] Update `parallel_executor.py` with TaskGroup implementation
- [ ] Add `_execute_with_semaphore_and_retries` helper method
- [ ] Add `_create_failed_result` and `_create_cancelled_result` helpers
- [ ] Update error handling to use `except* Exception`
- [ ] Replace `asyncio.wait_for` with `asyncio.timeout` context manager
- [ ] Add tests for cancellation propagation
- [ ] Add tests for ExceptionGroup handling
- [ ] Update documentation

## Testing

```python
async def test_taskgroup_cancellation():
    """Test that TaskGroup cancels all tasks when one fails."""
    executor = ParallelStepExecutor(max_parallel=4)
    
    async def failing_step(step: WorkflowStep) -> dict:
        if step.id == "step2":
            raise RuntimeError("Step 2 failed")
        await asyncio.sleep(0.1)
        return {}
    
    steps = [
        WorkflowStep(id="step1", agent="test", action="test"),
        WorkflowStep(id="step2", agent="test", action="test"),
        WorkflowStep(id="step3", agent="test", action="test"),
    ]
    
    state = WorkflowState(workflow_id="test", status="running")
    
    # Should raise exception and cancel other tasks
    with pytest.raises(RuntimeError):
        await executor.execute_parallel(
            steps=steps,
            execute_fn=failing_step,
            state=state,
        )
    
    # Verify other tasks were cancelled
    assert any(
        se.status == "cancelled"
        for se in state.step_executions
        if se.step_id in ["step1", "step3"]
    )
```

