# TappsCodingAgents - Detailed Design Document (Part 2)
## Implementation Details, Code Examples, and Troubleshooting

**Version:** 2.0  
**Date:** December 14, 2025  
**Continuation of Part 1**

---

## Table of Contents (Part 2)

1. [Detailed Agent Specifications](#detailed-agent-specifications)
2. [Communication Protocol Examples](#communication-protocol-examples)
3. [Expert Consultation Code Samples](#expert-consultation-code-samples)
4. [Workflow Execution Examples](#workflow-execution-examples)
5. [Configuration Reference](#configuration-reference)
6. [Troubleshooting Guide](#troubleshooting-guide)
7. [Best Practices](#best-practices)
8. [Appendices](#appendices)

---

## Detailed Agent Specifications

### Agent 1: Workflow Orchestration Agent

**Full Specification:**

```python
# tapps_agents/agents/orchestrator.py

from typing import Dict, List, Optional
import asyncio
from dataclasses import dataclass
from enum import Enum

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class Task:
    id: str
    agent: str
    execution_mode: str  # "foreground" or "background"
    inputs: Dict
    dependencies: List[str]
    status: TaskStatus
    priority: int  # 1-5, 5 is highest
    timeout: int  # seconds
    worktree: Optional[str]
    retry_count: int = 0
    max_retries: int = 2

class WorkflowOrchestrator:
    """Coordinates all agents and manages workflow execution"""
    
    def __init__(self):
        self.active_tasks: Dict[str, Task] = {}
        self.completed_tasks: Dict[str, Task] = {}
        self.worktrees: Dict[str, str] = {}  # worktree_name -> branch
        
    async def execute_workflow(self, workflow_yaml: str):
        """Execute a complete workflow from YAML definition"""
        workflow = self.parse_yaml(workflow_yaml)
        
        # Build dependency graph
        graph = self.build_dependency_graph(workflow.steps)
        
        # Execute tasks respecting dependencies
        while not self.all_tasks_complete(graph):
            # Find tasks ready to execute (dependencies met)
            ready_tasks = self.get_ready_tasks(graph)
            
            # Execute tasks in parallel (up to 8 concurrent)
            await self.execute_parallel(ready_tasks, max_parallel=8)
            
            # Check for failures
            failed = self.get_failed_tasks()
            if failed:
                await self.handle_failures(failed)
        
        # Aggregate results
        results = self.aggregate_results()
        
        # Cleanup worktrees
        await self.cleanup_worktrees()
        
        return results
    
    async def execute_parallel(self, tasks: List[Task], max_parallel: int):
        """Execute multiple tasks in parallel"""
        semaphore = asyncio.Semaphore(max_parallel)
        
        async def execute_with_semaphore(task):
            async with semaphore:
                return await self.execute_task(task)
        
        # Run tasks in parallel
        results = await asyncio.gather(*[
            execute_with_semaphore(task)
            for task in tasks
        ])
        
        return results
    
    async def execute_task(self, task: Task):
        """Execute a single task"""
        # Create worktree if needed
        if task.worktree:
            await self.create_worktree(task.worktree)
        
        # Write task to agent's inbox
        await self.write_inbox(task.agent, task)
        
        # Wait for completion or timeout
        result = await self.wait_for_completion(
            task, 
            timeout=task.timeout
        )
        
        # Update task status
        if result.success:
            task.status = TaskStatus.COMPLETED
            self.completed_tasks[task.id] = task
        else:
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                return await self.execute_task(task)  # Retry
            else:
                task.status = TaskStatus.FAILED
        
        return result
    
    async def create_worktree(self, name: str):
        """Create isolated git worktree for agent"""
        import subprocess
        
        worktree_path = f"worktree/{name}"
        branch_name = f"agent/{name}"
        
        # Create worktree
        subprocess.run([
            "git", "worktree", "add",
            "-b", branch_name,
            worktree_path,
            "HEAD"
        ], check=True)
        
        self.worktrees[name] = worktree_path
        
    async def merge_worktrees(self, sources: List[str], target: str):
        """Merge multiple worktree branches"""
        import subprocess
        
        # Checkout target branch
        subprocess.run(["git", "checkout", target], check=True)
        
        # Merge each source branch
        for source in sources:
            branch = f"agent/{source}"
            result = subprocess.run(
                ["git", "merge", "--no-ff", branch],
                capture_output=True
            )
            
            # Handle conflicts
            if result.returncode != 0:
                conflicts = await self.detect_conflicts()
                await self.resolve_conflicts(conflicts)
        
    async def resolve_conflicts(self, conflicts: List[str]):
        """Intelligent conflict resolution"""
        for conflict_file in conflicts:
            # Read conflicted file
            with open(conflict_file) as f:
                content = f.read()
            
            # Use Review Agent to resolve
            resolution = await self.call_agent(
                "review-agent",
                action="resolve_conflict",
                file=conflict_file,
                content=content
            )
            
            # Apply resolution
            with open(conflict_file, 'w') as f:
                f.write(resolution.resolved_content)
            
            # Mark as resolved
            subprocess.run(["git", "add", conflict_file])
    
    def build_dependency_graph(self, steps: List[Dict]) -> Dict:
        """Build task dependency graph"""
        graph = {}
        
        for step in steps:
            task_id = step['name']
            dependencies = step.get('depends_on', [])
            
            graph[task_id] = {
                'task': step,
                'dependencies': dependencies,
                'dependents': []
            }
        
        # Build reverse dependencies
        for task_id, node in graph.items():
            for dep in node['dependencies']:
                graph[dep]['dependents'].append(task_id)
        
        return graph
    
    def get_ready_tasks(self, graph: Dict) -> List[Task]:
        """Get tasks whose dependencies are satisfied"""
        ready = []
        
        for task_id, node in graph.items():
            # Check if all dependencies are completed
            deps_complete = all(
                dep in self.completed_tasks
                for dep in node['dependencies']
            )
            
            # Check if not already running/completed
            not_started = (
                task_id not in self.active_tasks and
                task_id not in self.completed_tasks
            )
            
            if deps_complete and not_started:
                task = self.create_task_from_node(node['task'])
                ready.append(task)
        
        # Sort by priority
        ready.sort(key=lambda t: t.priority, reverse=True)
        
        return ready
```

---

### Agent 2: Quality & Analysis Agent

**Full Specification:**

```python
# tapps_agents/agents/quality.py

from typing import Dict, List
from dataclasses import dataclass
import subprocess
import json

@dataclass
class QualityMetrics:
    complexity_score: float      # 0-10
    security_score: float         # 0-10
    maintainability_score: float  # 0-10
    test_coverage_score: float    # 0-10
    performance_score: float      # 0-10
    overall_score: float          # weighted average
    
    issues: List[Dict]
    recommendations: List[Dict]

class QualityAnalysisAgent:
    """Analyzes code quality using multiple tools"""
    
    def __init__(self):
        self.tools = {
            'ruff': self.run_ruff,
            'mypy': self.run_mypy,
            'bandit': self.run_bandit,
            'radon': self.run_radon,
            'jscpd': self.run_jscpd
        }
    
    async def analyze(self, code_path: str) -> QualityMetrics:
        """Run complete quality analysis"""
        
        # Run all tools in parallel
        results = await asyncio.gather(*[
            tool_func(code_path)
            for tool_func in self.tools.values()
        ])
        
        # Parse results
        ruff_issues = results[0]
        mypy_issues = results[1]
        bandit_issues = results[2]
        radon_metrics = results[3]
        duplication = results[4]
        
        # Calculate scores
        complexity_score = self.calculate_complexity_score(radon_metrics)
        security_score = self.calculate_security_score(bandit_issues)
        maintainability_score = self.calculate_maintainability_score(
            radon_metrics
        )
        performance_score = self.calculate_performance_score(
            radon_metrics, 
            ruff_issues
        )
        
        # Test coverage (read from existing report)
        coverage_score = await self.get_coverage_score()
        
        # Calculate weighted overall score
        overall = (
            complexity_score * 0.20 +
            security_score * 0.25 +
            maintainability_score * 0.20 +
            coverage_score * 0.20 +
            performance_score * 0.15
        )
        
        # Aggregate issues
        all_issues = (
            ruff_issues + mypy_issues + bandit_issues
        )
        
        # Generate recommendations
        recommendations = self.generate_recommendations(
            all_issues, 
            radon_metrics
        )
        
        return QualityMetrics(
            complexity_score=complexity_score,
            security_score=security_score,
            maintainability_score=maintainability_score,
            test_coverage_score=coverage_score,
            performance_score=performance_score,
            overall_score=overall,
            issues=all_issues,
            recommendations=recommendations
        )
    
    async def run_ruff(self, code_path: str) -> List[Dict]:
        """Run Ruff linter"""
        result = subprocess.run(
            ["ruff", "check", code_path, "--output-format", "json"],
            capture_output=True,
            text=True
        )
        
        issues = json.loads(result.stdout) if result.stdout else []
        
        return [
            {
                "tool": "ruff",
                "severity": self.map_ruff_severity(issue),
                "file": issue['filename'],
                "line": issue['location']['row'],
                "message": issue['message'],
                "code": issue['code']
            }
            for issue in issues
        ]
    
    async def run_bandit(self, code_path: str) -> List[Dict]:
        """Run Bandit security scanner"""
        result = subprocess.run(
            ["bandit", "-r", code_path, "-f", "json"],
            capture_output=True,
            text=True
        )
        
        data = json.loads(result.stdout) if result.stdout else {}
        issues = data.get('results', [])
        
        return [
            {
                "tool": "bandit",
                "severity": issue['issue_severity'].lower(),
                "file": issue['filename'],
                "line": issue['line_number'],
                "message": issue['issue_text'],
                "confidence": issue['issue_confidence']
            }
            for issue in issues
        ]
    
    async def run_radon(self, code_path: str) -> Dict:
        """Run Radon complexity and maintainability analysis"""
        # Cyclomatic complexity
        cc_result = subprocess.run(
            ["radon", "cc", code_path, "-j"],
            capture_output=True,
            text=True
        )
        complexity = json.loads(cc_result.stdout) if cc_result.stdout else {}
        
        # Maintainability index
        mi_result = subprocess.run(
            ["radon", "mi", code_path, "-j"],
            capture_output=True,
            text=True
        )
        maintainability = json.loads(mi_result.stdout) if mi_result.stdout else {}
        
        return {
            "complexity": complexity,
            "maintainability": maintainability
        }
    
    def calculate_complexity_score(self, radon_metrics: Dict) -> float:
        """Calculate complexity score from Radon metrics"""
        complexity_data = radon_metrics.get('complexity', {})
        
        if not complexity_data:
            return 10.0
        
        # Get average cyclomatic complexity
        all_complexities = []
        for file_data in complexity_data.values():
            for func_data in file_data:
                all_complexities.append(func_data['complexity'])
        
        if not all_complexities:
            return 10.0
        
        avg_complexity = sum(all_complexities) / len(all_complexities)
        
        # Score: 10 = complexity 1-5, 0 = complexity 20+
        # Linear interpolation
        if avg_complexity <= 5:
            return 10.0
        elif avg_complexity >= 20:
            return 0.0
        else:
            return 10.0 - ((avg_complexity - 5) / 15) * 10
    
    def calculate_security_score(self, bandit_issues: List[Dict]) -> float:
        """Calculate security score from Bandit issues"""
        if not bandit_issues:
            return 10.0
        
        # Weight by severity
        severity_weights = {
            "high": -3.0,
            "medium": -1.5,
            "low": -0.5
        }
        
        deductions = sum(
            severity_weights.get(issue['severity'], 0)
            for issue in bandit_issues
        )
        
        score = max(0, 10.0 + deductions)
        return score
    
    def generate_recommendations(
        self, 
        issues: List[Dict], 
        radon_metrics: Dict
    ) -> List[Dict]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Security recommendations
        security_issues = [i for i in issues if i['tool'] == 'bandit']
        if security_issues:
            recommendations.append({
                "priority": "high",
                "category": "security",
                "message": f"Found {len(security_issues)} security issues. Review and fix immediately.",
                "details": security_issues[:3]  # Top 3
            })
        
        # Complexity recommendations
        complex_functions = self.find_complex_functions(radon_metrics)
        if complex_functions:
            recommendations.append({
                "priority": "medium",
                "category": "complexity",
                "message": "Refactor complex functions to improve maintainability",
                "details": complex_functions[:5]
            })
        
        return recommendations
```

---

## Communication Protocol Examples

### Message Format Specifications

**Task Assignment Message:**
```json
{
  "message_type": "task_assignment",
  "message_id": "msg_12345",
  "timestamp": "2025-12-14T10:30:00Z",
  "from": "orchestrator",
  "to": "quality-001",
  
  "task": {
    "task_id": "analyze-security-001",
    "priority": "high",
    "timeout_seconds": 1200,
    "retry_policy": {
      "max_retries": 2,
      "backoff_seconds": 60
    }
  },
  
  "inputs": {
    "code_path": "worktree/code-001",
    "config_file": ".ruff.toml",
    "focus": ["security", "complexity"]
  },
  
  "dependencies": {
    "required": ["code-implementation-001"],
    "optional": []
  },
  
  "outputs": {
    "required": [
      ".tapps-agents/state/quality_results.json"
    ],
    "optional": [
      ".tapps-agents/reports/quality/latest.html"
    ]
  }
}
```

**Status Update Message:**
```json
{
  "message_type": "status_update",
  "message_id": "msg_12346",
  "timestamp": "2025-12-14T10:32:15Z",
  "from": "quality-001",
  "to": "orchestrator",
  
  "task_id": "analyze-security-001",
  "status": "in_progress",
  "progress_percent": 35,
  
  "current_step": "Running Bandit security scan",
  "estimated_completion": "2025-12-14T10:38:00Z",
  
  "metrics": {
    "files_analyzed": 23,
    "total_files": 67,
    "issues_found": 5
  }
}
```

**Completion Message:**
```json
{
  "message_type": "task_completed",
  "message_id": "msg_12347",
  "timestamp": "2025-12-14T10:42:30Z",
  "from": "quality-001",
  "to": "orchestrator",
  
  "task_id": "analyze-security-001",
  "status": "completed",
  "duration_seconds": 730,
  
  "results": {
    "overall_score": 8.5,
    "output_files": [
      ".tapps-agents/state/quality_results.json",
      ".tapps-agents/reports/quality/latest.html"
    ]
  },
  
  "next_recommended_agents": [
    "review-001"
  ]
}
```

---

## Expert Consultation Code Samples

### Complete Expert Consultation Example

```python
# tapps_agents/experts/registry.py

from typing import List, Dict, Optional
import asyncio
from dataclasses import dataclass

@dataclass
class ExpertRecommendation:
    expert_name: str
    weight: float
    confidence: float
    recommendation: Dict
    knowledge_sources: List[str]

class ExpertRegistry:
    """Manages all experts and consultation"""
    
    def __init__(self):
        self.industry_experts = {}
        self.builtin_experts = {}
        self.load_experts()
    
    async def consult_experts(
        self, 
        query: str, 
        context: Dict,
        max_experts: int = 5
    ) -> List[ExpertRecommendation]:
        """Consult relevant experts for a query"""
        
        # 1. Identify relevant experts
        relevant = self.get_relevant_experts(query, context, max_experts)
        
        # 2. Query experts in parallel
        tasks = [
            self.query_expert(expert, query, context)
            for expert in relevant
        ]
        
        recommendations = await asyncio.gather(*tasks)
        
        return recommendations
    
    def get_relevant_experts(
        self, 
        query: str, 
        context: Dict,
        max_experts: int
    ) -> List['Expert']:
        """Identify which experts should be consulted"""
        
        relevant = []
        
        # Always include primary industry expert
        primary = self.get_primary_industry_expert()
        if primary:
            relevant.append(primary)
        
        # Check triggers for other industry experts
        for expert in self.industry_experts.values():
            if expert == primary:
                continue
            
            if expert.should_consult(query, context):
                relevant.append(expert)
        
        # Check triggers for builtin experts
        for expert in self.builtin_experts.values():
            if expert.should_consult(query, context):
                relevant.append(expert)
        
        # Sort by relevance and weight
        relevant.sort(
            key=lambda e: (e.relevance_score(query, context), e.weight),
            reverse=True
        )
        
        return relevant[:max_experts]
    
    async def query_expert(
        self, 
        expert: 'Expert', 
        query: str, 
        context: Dict
    ) -> ExpertRecommendation:
        """Query a single expert"""
        
        # Retrieve relevant knowledge from RAG
        knowledge = await expert.retrieve_knowledge(query, top_k=5)
        
        # Get expert recommendation
        recommendation = await expert.consult(
            query=query,
            context=context,
            knowledge=knowledge
        )
        
        return ExpertRecommendation(
            expert_name=expert.name,
            weight=expert.weight,
            confidence=recommendation.confidence,
            recommendation=recommendation.data,
            knowledge_sources=[k.source for k in knowledge]
        )
    
    def weighted_decision(
        self, 
        recommendations: List[ExpertRecommendation]
    ) -> Dict:
        """Make weighted decision from expert recommendations"""
        
        # Calculate weighted scores
        weighted_scores = {}
        for rec in recommendations:
            score = rec.weight * rec.confidence
            weighted_scores[rec.expert_name] = score
        
        # Get best expert
        best_expert_name = max(weighted_scores, key=weighted_scores.get)
        best_rec = next(
            r for r in recommendations 
            if r.expert_name == best_expert_name
        )
        
        # Combine all recommendations intelligently
        combined = self.combine_recommendations(recommendations)
        
        return {
            "primary_recommendation": best_rec.recommendation,
            "primary_expert": best_expert_name,
            "confidence": weighted_scores[best_expert_name],
            "all_recommendations": [
                {
                    "expert": r.expert_name,
                    "weight": r.weight,
                    "confidence": r.confidence,
                    "recommendation": r.recommendation
                }
                for r in recommendations
            ],
            "combined_guidance": combined
        }
    
    def combine_recommendations(
        self, 
        recommendations: List[ExpertRecommendation]
    ) -> Dict:
        """Intelligently combine multiple expert recommendations"""
        
        combined = {
            "architecture": {},
            "security": {},
            "compliance": {},
            "performance": {},
            "implementation": {}
        }
        
        for rec in recommendations:
            expert_type = rec.expert_name
            data = rec.recommendation
            
            # Merge based on expert type
            if "architecture" in data:
                combined["architecture"].update(data["architecture"])
            
            if "security" in data:
                combined["security"].update(data["security"])
            
            if "compliance" in data:
                if "compliance" not in combined:
                    combined["compliance"] = []
                combined["compliance"].extend(data["compliance"])
            
            # ... continue for other categories
        
        return combined


class Expert:
    """Base expert class"""
    
    def __init__(self, config: Dict):
        self.name = config['name']
        self.type = config['type']
        self.domain = config['domain']
        self.weight = config.get('weight', 0.0)
        self.capabilities = config.get('capabilities', [])
        self.triggers = config.get('triggers', {})
        self.rag = RAGSystem(config.get('rag', {}))
    
    def should_consult(self, query: str, context: Dict) -> bool:
        """Check if this expert should be consulted"""
        
        # Check keyword triggers
        keywords = self.triggers.get('keywords', [])
        if any(kw.lower() in query.lower() for kw in keywords):
            return True
        
        # Check context triggers
        contexts = self.triggers.get('contexts', [])
        context_type = context.get('type', '')
        if context_type in contexts:
            return True
        
        # Check file pattern triggers
        file_patterns = self.triggers.get('file_patterns', [])
        files = context.get('files', [])
        if any(
            self.matches_pattern(f, pattern)
            for f in files
            for pattern in file_patterns
        ):
            return True
        
        return False
    
    def relevance_score(self, query: str, context: Dict) -> float:
        """Calculate how relevant this expert is"""
        score = 0.0
        
        # Keyword matches
        keywords = self.triggers.get('keywords', [])
        matches = sum(
            1 for kw in keywords 
            if kw.lower() in query.lower()
        )
        score += matches * 0.2
        
        # Context match
        if context.get('type') in self.triggers.get('contexts', []):
            score += 0.5
        
        # Base weight
        score += self.weight
        
        return score
    
    async def retrieve_knowledge(
        self, 
        query: str, 
        top_k: int = 5
    ) -> List[Dict]:
        """Retrieve relevant knowledge from RAG"""
        return await self.rag.query(query, top_k=top_k)
    
    async def consult(
        self, 
        query: str, 
        context: Dict,
        knowledge: List[Dict]
    ) -> 'Recommendation':
        """Generate expert recommendation"""
        
        # Construct prompt with knowledge
        prompt = self.build_consultation_prompt(
            query, 
            context, 
            knowledge
        )
        
        # Call LLM (via Cursor's model)
        response = await self.call_llm(prompt)
        
        # Parse and structure response
        recommendation = self.parse_recommendation(response)
        
        # Calculate confidence
        confidence = self.calculate_confidence(
            recommendation, 
            knowledge
        )
        
        return Recommendation(
            data=recommendation,
            confidence=confidence,
            knowledge_used=knowledge
        )
```

---

## Workflow Execution Examples

### Example 1: Simple Feature Implementation

```yaml
# .tapps-agents/workflows/simple-feature.yaml

workflow:
  name: simple-feature
  description: "Implement a simple feature with minimal steps"
  
  inputs:
    - name: feature_name
      type: string
      required: true
  
  steps:
    - name: implement
      agent: code-agent
      execution: foreground
      inputs:
        description: "{{feature_name}}"
      timeout: 1800
      
    - name: test
      agent: testing-agent
      execution: background
      depends_on: [implement]
      timeout: 600
      
    - name: review
      agent: review-agent
      execution: foreground
      depends_on: [test]
      timeout: 300
```

**Execution:**
```bash
tapps-agents workflow run \
  --workflow simple-feature \
  --input feature_name="Add logout button"
```

---

### Example 2: Complex Multi-Agent Workflow

```yaml
# .tapps-agents/workflows/complex-feature.yaml

workflow:
  name: complex-feature
  description: "Full SDLC workflow with all agents"
  
  steps:
    - name: analyze_requirements
      agent: planning-agent
      execution: foreground
      
    - name: create_architecture
      agent: design-agent
      execution: foreground
      depends_on: [analyze_requirements]
      
    - name: parallel_implementation
      type: parallel
      depends_on: [create_architecture]
      tasks:
        - name: code
          agent: code-agent
          worktree: code-001
          
        - name: tests
          agent: testing-agent
          worktree: test-001
          
        - name: docs
          agent: docs-agent
          worktree: docs-001
          
        - name: warm_cache
          agent: context-agent
          priority: low
    
    - name: quality_check
      agent: quality-agent
      execution: background
      depends_on: [parallel_implementation.code]
      
    - name: run_tests
      agent: testing-agent
      execution: background
      depends_on:
        - parallel_implementation.code
        - parallel_implementation.tests
      
    - name: code_review
      agent: review-agent
      execution: foreground
      depends_on: [quality_check, run_tests]
      
    - name: deploy_prep
      agent: ops-agent
      execution: background
      depends_on: [code_review]
      
    - name: create_pr
      agent: orchestrator
      depends_on: [deploy_prep]
      actions:
        - merge_worktrees
        - create_pull_request
```

---

## Configuration Reference

### Project Configuration

**`.tapps-agents/config/project.yaml`**
```yaml
project:
  name: "My Application"
  version: "2.0.0"
  type: "web_application"  # or "api", "library", "cli"
  
  # Technology stack
  stack:
    backend: "fastapi"
    frontend: "react"
    database: "postgresql"
    cache: "redis"
  
  # Project profile
  profile:
    deployment_type: "cloud_native"  # or "on_premise", "hybrid"
    tenancy: "multi_tenant"  # or "single_tenant"
    user_scale: "medium"  # "small" (<1k), "medium" (<10k), "large" (10k+)
    compliance: ["HIPAA", "SOC2"]
    security_posture: "high"  # "low", "medium", "high"
    
  # Quality thresholds
  quality:
    min_overall_score: 8.0
    min_security_score: 8.5
    min_test_coverage: 80.0
    max_complexity: 10
    
  # Agent configuration
  agents:
    max_parallel: 8
    default_timeout: 1800
    retry_policy:
      max_retries: 2
      backoff_seconds: 60
```

### Agent Configuration

**`.tapps-agents/config/agents.yaml`**
```yaml
agents:
  orchestrator:
    enabled: true
    execution: "foreground"
    
  quality:
    enabled: true
    execution: "background"
    tools:
      - ruff
      - mypy
      - bandit
      - radon
      
  testing:
    enabled: true
    execution: "background"
    frameworks:
      - pytest
      - jest
    coverage_target: 80
    
  code:
    enabled: true
    execution: "foreground"
    style: "black"
    type_hints: true
    
  design:
    enabled: true
    execution: "foreground"
    consult_experts: true
    max_experts: 5
```

---

## Troubleshooting Guide

### Common Issues and Solutions

#### Issue 1: Worktree Merge Conflicts

**Symptom:**
```
error: Entry 'src/main.py' overlaps with 'src/main.py'
Cannot merge worktree branches
```

**Solution:**
```bash
# 1. Check which agents modified the file
git log --all --source -- src/main.py

# 2. Use Review Agent to resolve
tapps-agents agent run \
  --agent review \
  --action resolve_conflict \
  --file src/main.py

# 3. Manual resolution if needed
git checkout --ours src/main.py  # Keep main version
# or
git checkout --theirs src/main.py  # Keep agent version
git add src/main.py
```

---

#### Issue 2: Agent Timeout

**Symptom:**
```
Task 'quality-001' exceeded timeout of 1800 seconds
Status: FAILED
```

**Solution:**
```yaml
# Increase timeout in workflow
steps:
  - name: quality
    timeout: 3600  # 60 minutes instead of 30
    
# Or split into smaller tasks
steps:
  - name: quality_lint
    timeout: 900
  - name: quality_security
    timeout: 900
```

---

#### Issue 3: Expert RAG Index Missing

**Symptom:**
```
ExpertNotFoundError: No RAG index for expert 'healthcare'
```

**Solution:**
```bash
# Build RAG index
tapps-agents rag build --expert healthcare

# Verify index exists
ls -la .tapps-agents/experts/industry/healthcare/rag/
```

---

#### Issue 4: Context7 Cache Miss

**Symptom:**
```
Cache miss rate: 95%
Token usage high
```

**Solution:**
```bash
# Pre-populate cache
tapps-agents context7 populate \
  --libraries fastapi,pytest,pydantic \
  --force-refresh

# Verify cache
tapps-agents context7 stats

# Expected output:
# Cache hit rate: 87%
# Cached libraries: 5
# Total chunks: 2,847
```

---

## Best Practices

### 1. Workflow Design

**DO:**
- Break complex features into small, atomic tasks
- Use parallel execution where possible
- Set appropriate timeouts (2x expected time)
- Include retry logic for flaky operations
- Use worktrees for parallel code changes

**DON'T:**
- Create circular dependencies
- Run more than 8 agents simultaneously
- Skip quality checks to save time
- Merge without review
- Hardcode file paths

### 2. Expert Configuration

**DO:**
- Populate knowledge bases thoroughly
- Use meaningful trigger keywords
- Set appropriate confidence thresholds
- Weight primary expert correctly (51%)
- Regularly update knowledge

**DON'T:**
- Create experts without knowledge
- Use too many experts (max 5 per query)
- Ignore expert recommendations
- Forget to rebuild RAG after updates
- Mix industry and technical experts

### 3. Agent Communication

**DO:**
- Use structured JSON messages
- Include timestamps and IDs
- Provide clear error messages
- Log all agent interactions
- Clean up state files

**DON'T:**
- Use unstructured text
- Forget message acknowledgments
- Leave orphaned worktrees
- Skip status updates
- Ignore failed messages

---

## Appendices

### Appendix A: File Structure Reference

Complete `.tapps-agents/` directory structure:

```
.tapps-agents/
├── config/
│   ├── project.yaml
│   ├── agents.yaml
│   └── experts.yaml
├── experts/
│   ├── industry/
│   │   └── healthcare/
│   │       ├── expert.yaml
│   │       ├── knowledge/
│   │       └── rag/
│   └── builtin/
│       ├── security/
│       └── ... (15 more)
├── context7/
│   ├── cache/
│   └── stats/
├── state/
│   ├── quality_results.json
│   ├── test_results.json
│   └── workflow_state.json
├── messages/
│   ├── inbox/
│   └── outbox/
├── workflows/
│   ├── simple-feature.yaml
│   └── complex-feature.yaml
└── reports/
    ├── quality/
    ├── coverage/
    └── review/
```

### Appendix B: API Quick Reference

```python
# Workflow execution
tapps-agents workflow run --workflow <name> --input key=value

# Agent execution
tapps-agents agent run --agent <name> --action <action>

# Expert management
tapps-agents expert create --name <name> --type industry
tapps-agents expert list
tapps-agents rag build --expert <name>

# Context7 operations
tapps-agents context7 populate --libraries lib1,lib2
tapps-agents context7 stats
tapps-agents context7 clear

# Monitoring
tapps-agents workflow status --id <id>
tapps-agents agent status --id <id>
tapps-agents logs --agent <name> --tail 100
```

### Appendix C: Recommended Reading

- **Cursor Documentation**: https://cursor.com/docs
- **TappsCodingAgents GitHub**: https://github.com/wtthornton/TappsCodingAgents
- **Multi-Agent Systems**: "Multi-Agent Systems" by Wooldridge
- **RAG Systems**: "Retrieval-Augmented Generation" papers
- **Workflow Orchestration**: Apache Airflow documentation

---

## Conclusion

This detailed design document provides:

1. ✅ Complete architecture specifications
2. ✅ All 11 agent implementations
3. ✅ Communication protocols
4. ✅ Expert system design
5. ✅ RAG implementation guide
6. ✅ Workflow orchestration
7. ✅ Configuration reference
8. ✅ Troubleshooting guide
9. ✅ Best practices

**Implementation Timeline:** 12 weeks  
**Expected Outcomes:** 60% faster development, 8.0+ code quality  
**Team Size:** 2-3 developers  

**Next Steps:**
1. Review and approve design
2. Set up development environment
3. Begin Phase 1 (Foundation)
4. Create proof-of-concept with 2-3 agents
5. Iterate based on feedback

---

*End of Detailed Design Document*
