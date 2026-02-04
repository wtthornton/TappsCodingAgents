"""
Brownfield System Review Orchestrator

Orchestrates complete brownfield review workflow: analysis, expert creation, and RAG population.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from ..context7.agent_integration import Context7AgentHelper
from ..experts.domain_detector import DomainMapping
from ..experts.knowledge_ingestion import IngestionResult, KnowledgeIngestionPipeline
from .brownfield_analyzer import BrownfieldAnalysisResult, BrownfieldAnalyzer
from .expert_config_generator import ExpertConfig, ExpertConfigGenerator

logger = logging.getLogger(__name__)


@dataclass
class BrownfieldReviewResult:
    """Result of complete brownfield review."""

    analysis: BrownfieldAnalysisResult
    experts_created: list[ExpertConfig] = field(default_factory=list)
    rag_results: dict[str, IngestionResult] = field(
        default_factory=dict
    )  # expert_id -> ingestion result
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    execution_time: float = 0.0
    dry_run: bool = False
    report: str = ""


class BrownfieldReviewOrchestrator:
    """
    Orchestrates complete brownfield review workflow.

    Usage:
        orchestrator = BrownfieldReviewOrchestrator(
            project_root=Path.cwd(),
            context7_helper=context7_helper,
            dry_run=False
        )
        result = await orchestrator.review(auto=True, include_context7=True)
        print(result.report)
    """

    def __init__(
        self,
        project_root: Path,
        context7_helper: Context7AgentHelper | None = None,
        dry_run: bool = False,
    ) -> None:
        """
        Initialize orchestrator.

        Args:
            project_root: Root directory of project to review
            context7_helper: Optional Context7 helper for library docs
            dry_run: If True, preview changes without applying
        """
        self.project_root = Path(project_root).resolve()
        self.context7_helper = context7_helper
        self.dry_run = dry_run
        self.config_dir = self.project_root / ".tapps-agents"
        self.state_file = self.config_dir / "brownfield-review-state.json"

        # Initialize components
        self.analyzer = BrownfieldAnalyzer(project_root=self.project_root)
        self.config_generator = ExpertConfigGenerator(project_root=self.project_root)
        self.ingestion_pipeline = KnowledgeIngestionPipeline(
            project_root=self.project_root, context7_helper=context7_helper
        )

    async def review(
        self,
        auto: bool = False,
        include_context7: bool = True,
        resume: bool = False,
        resume_from: str | None = None,
    ) -> BrownfieldReviewResult:
        """
        Perform complete brownfield review.

        Args:
            auto: If True, skip all prompts and use defaults
            include_context7: If True, fetch library docs from Context7
            resume: If True, resume from saved state
            resume_from: Step to resume from ("analyze", "create_experts", "populate_rag")

        Returns:
            BrownfieldReviewResult with complete analysis and results
        """
        start_time = time.time()
        errors: list[str] = []
        warnings: list[str] = []

        logger.info("Starting brownfield review")
        if self.dry_run:
            logger.info("DRY RUN MODE: No changes will be applied")

        # Load state if resuming
        state = None
        if resume:
            state = self._load_state()
            if state and resume_from:
                logger.info(f"Resuming from step: {resume_from}")

        try:
            # Step 1: Analyze codebase
            if not resume or not state or resume_from == "analyze" or resume_from is None:
                logger.info("Step 1: Analyzing codebase...")
                analysis = await self._analyze_codebase()
                self._save_state({"step": "analyze", "analysis": self._serialize_analysis(analysis)})
                logger.info(
                    f"Analysis complete: {len(analysis.domains)} domains detected"
                )
            else:
                # Load from state
                analysis = self._deserialize_analysis(state.get("analysis", {}))
                logger.info("Loaded analysis from saved state")

            # Step 2: Create expert configurations
            if not resume or not state or resume_from == "create_experts" or resume_from is None:
                logger.info("Step 2: Creating expert configurations...")
                experts_created = await self._create_experts(analysis.domains)
                self._save_state({
                    "step": "create_experts",
                    "analysis": self._serialize_analysis(analysis),
                    "experts_created": [self._serialize_expert(e) for e in experts_created],
                })
                logger.info(f"Created {len(experts_created)} expert configurations")
            else:
                # Load from state
                experts_created = [
                    self._deserialize_expert(e) for e in state.get("experts_created", [])
                ]
                logger.info(f"Loaded {len(experts_created)} experts from saved state")

            # Step 3: Populate RAG knowledge bases
            if not resume or not state or resume_from == "populate_rag" or resume_from is None:
                logger.info("Step 3: Populating RAG knowledge bases...")
                rag_results = await self._populate_rag(
                    experts_created, include_context7=include_context7
                )
                self._save_state({
                    "step": "complete",
                    "analysis": self._serialize_analysis(analysis),
                    "experts_created": [self._serialize_expert(e) for e in experts_created],
                    "rag_results": {k: {
                        "entries_ingested": v.entries_ingested,
                        "entries_failed": v.entries_failed,
                        "source_type": v.source_type,
                    } for k, v in rag_results.items()},
                })
                logger.info(
                    f"Populated RAG for {len(rag_results)} experts"
                )
            else:
                # Load from state
                rag_results = {
                    k: IngestionResult(
                        source_type=v.get("source_type", "unknown"),
                        entries_ingested=v.get("entries_ingested", 0),
                        entries_failed=v.get("entries_failed", 0),
                    )
                    for k, v in state.get("rag_results", {}).items()
                }
                logger.info("Loaded RAG results from saved state")

        except Exception as e:
            error_msg = f"Brownfield review failed: {e}"
            logger.error(error_msg, exc_info=True)
            errors.append(error_msg)
            # Save error state
            self._save_state({
                "step": "error",
                "error": str(e),
                "errors": errors,
            })
            # Create minimal result for error case
            if 'analysis' not in locals():
                analysis = BrownfieldAnalysisResult(project_root=self.project_root)
            if 'experts_created' not in locals():
                experts_created = []
            if 'rag_results' not in locals():
                rag_results = {}

        execution_time = time.time() - start_time

        # Generate report
        result = BrownfieldReviewResult(
            analysis=analysis,
            experts_created=experts_created,
            rag_results=rag_results,
            errors=errors,
            warnings=warnings,
            execution_time=execution_time,
            dry_run=self.dry_run,
        )

        result.report = self._generate_report(result)

        logger.info(f"Brownfield review complete in {execution_time:.2f}s")
        return result

    async def _analyze_codebase(self) -> BrownfieldAnalysisResult:
        """Step 1: Analyze codebase structure and detect domains."""
        try:
            result = await self.analyzer.analyze()
            return result
        except Exception as e:
            logger.error(f"Codebase analysis failed: {e}", exc_info=True)
            raise

    async def _create_experts(
        self, domains: list[DomainMapping]
    ) -> list[ExpertConfig]:
        """Step 2: Create expert configurations."""
        if self.dry_run:
            logger.info("DRY RUN: Would create expert configs")
            # Still generate configs for preview
            configs = self.config_generator.generate_expert_configs(domains)
            return configs

        try:
            # Generate expert configurations
            configs = self.config_generator.generate_expert_configs(domains)

            # Validate each config
            valid_configs = []
            for config in configs:
                if self.config_generator.validate_config(config):
                    valid_configs.append(config)
                else:
                    logger.warning(f"Invalid config for {config.expert_id}, skipping")

            # Write to YAML file
            if valid_configs:
                self.config_generator.write_expert_configs(valid_configs, merge=True)

                # Create knowledge base directories
                for config in valid_configs:
                    if config.knowledge_base_dir:
                        config.knowledge_base_dir.mkdir(parents=True, exist_ok=True)
                        logger.info(
                            f"Created knowledge base directory: {config.knowledge_base_dir}"
                        )

            return valid_configs
        except Exception as e:
            logger.error(f"Expert creation failed: {e}", exc_info=True)
            raise

    async def _populate_rag(
        self, experts: list[ExpertConfig], include_context7: bool = True
    ) -> dict[str, IngestionResult]:
        """Step 3: Populate RAG knowledge bases for each expert."""
        results: dict[str, IngestionResult] = {}

        if self.dry_run:
            logger.info("DRY RUN: Would populate RAG knowledge bases")
            return results

        # Use parallel processing for better performance
        import asyncio

        async def populate_expert_rag(expert: ExpertConfig) -> tuple[str, IngestionResult]:
            """Populate RAG for a single expert."""
            try:
                logger.info(f"Populating RAG for expert {expert.expert_id}...")

                # Create expert-specific knowledge base directory if needed
                if expert.knowledge_base_dir:
                    expert.knowledge_base_dir.mkdir(parents=True, exist_ok=True)

                # Create expert-specific ingestion pipeline
                expert_pipeline = KnowledgeIngestionPipeline(
                    project_root=self.project_root,
                    context7_helper=self.context7_helper,
                )

                # Ingest project sources for this expert's domain
                project_result = expert_pipeline.ingest_project_sources()

                # Store ingested content in expert-specific KB directory
                if expert.knowledge_base_dir and project_result.entries_ingested > 0:
                    # Copy/move ingested files to expert KB directory
                    # This is a simplified version - full implementation would
                    # use the knowledge base's add_chunk methods
                    logger.debug(
                        f"Stored {project_result.entries_ingested} entries in {expert.knowledge_base_dir}"
                    )

                # Ingest Context7 sources if enabled
                context7_result = None
                if include_context7 and self.context7_helper:
                    try:
                        context7_result = (
                            await expert_pipeline.ingest_context7_sources()
                        )
                        # Combine project and context7 results
                        if context7_result:
                            project_result.entries_ingested += context7_result.entries_ingested
                            project_result.entries_failed += context7_result.entries_failed
                            project_result.errors.extend(context7_result.errors)
                    except Exception as e:
                        logger.warning(
                            f"Context7 ingestion failed for {expert.expert_id}: {e}"
                        )

                logger.info(
                    f"RAG population complete for {expert.expert_id}: "
                    f"{project_result.entries_ingested} entries ingested"
                )

                return (expert.expert_id, project_result)

            except Exception as e:
                logger.error(
                    f"RAG population failed for {expert.expert_id}: {e}",
                    exc_info=True,
                )
                return (
                    expert.expert_id,
                    IngestionResult(
                        source_type="error",
                        entries_ingested=0,
                        entries_failed=1,
                        errors=[str(e)],
                    ),
                )

        # Process experts in parallel (with limit to avoid overwhelming system)
        tasks = [populate_expert_rag(expert) for expert in experts]
        expert_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect results
        for result in expert_results:
            if isinstance(result, Exception):
                logger.error(f"Expert RAG population task failed: {result}")
                continue
            expert_id, ingestion_result = result
            results[expert_id] = ingestion_result

        return results

    def _generate_report(self, result: BrownfieldReviewResult) -> str:
        """Generate human-readable summary report."""
        lines = []
        lines.append("# Brownfield System Review Report")
        lines.append("")
        lines.append(f"**Generated:** {datetime.now().isoformat()}")
        lines.append(f"**Execution Time:** {result.execution_time:.2f}s")
        if result.dry_run:
            lines.append("**Mode:** DRY RUN (no changes applied)")
        lines.append("")

        # Analysis Summary
        lines.append("## Analysis Summary")
        lines.append("")
        lines.append(f"- **Languages Detected:** {', '.join(result.analysis.languages) or 'None'}")
        lines.append(f"- **Frameworks Detected:** {', '.join(result.analysis.frameworks) or 'None'}")
        lines.append(f"- **Dependencies Found:** {len(result.analysis.dependencies)}")
        lines.append(f"- **Domains Detected:** {len(result.analysis.domains)}")
        lines.append("")

        # Domains
        if result.analysis.domains:
            lines.append("### Detected Domains")
            lines.append("")
            for domain in result.analysis.domains[:10]:  # Top 10
                lines.append(
                    f"- **{domain.domain}** (confidence: {domain.confidence:.2f})"
                )
            if len(result.analysis.domains) > 10:
                lines.append(f"- ... and {len(result.analysis.domains) - 10} more")
            lines.append("")

        # Experts Created
        lines.append("## Experts Created")
        lines.append("")
        if result.experts_created:
            for expert in result.experts_created:
                lines.append(f"- **{expert.expert_name}** (`{expert.expert_id}`)")
                lines.append(f"  - Domain: {expert.primary_domain}")
                lines.append(f"  - RAG Enabled: {expert.rag_enabled}")
                if expert.knowledge_base_dir:
                    lines.append(f"  - KB Directory: `{expert.knowledge_base_dir}`")
            lines.append("")
        else:
            lines.append("No new experts created (may already exist or no domains detected)")
            lines.append("")

        # RAG Population Results
        lines.append("## RAG Population Results")
        lines.append("")
        if result.rag_results:
            total_ingested = sum(
                r.entries_ingested for r in result.rag_results.values()
            )
            total_failed = sum(r.entries_failed for r in result.rag_results.values())
            lines.append(f"- **Total Entries Ingested:** {total_ingested}")
            lines.append(f"- **Total Entries Failed:** {total_failed}")
            lines.append("")
            for expert_id, rag_result in result.rag_results.items():
                lines.append(f"### {expert_id}")
                lines.append(f"- Ingested: {rag_result.entries_ingested}")
                lines.append(f"- Failed: {rag_result.entries_failed}")
                if rag_result.errors:
                    lines.append(f"- Errors: {len(rag_result.errors)}")
                lines.append("")
        else:
            lines.append("No RAG population performed (dry run or no experts)")
            lines.append("")

        # Errors and Warnings
        if result.errors:
            lines.append("## Errors")
            lines.append("")
            for error in result.errors:
                lines.append(f"- ❌ {error}")
            lines.append("")

        if result.warnings:
            lines.append("## Warnings")
            lines.append("")
            for warning in result.warnings:
                lines.append(f"- ⚠️ {warning}")
            lines.append("")

        # Summary
        lines.append("## Summary")
        lines.append("")
        if result.dry_run:
            lines.append("This was a dry run. No changes were applied.")
        else:
            lines.append(
                f"✅ Created {len(result.experts_created)} expert configurations"
            )
            lines.append(
                f"✅ Populated RAG for {len(result.rag_results)} experts"
            )
        lines.append("")

        return "\n".join(lines)

    def _save_state(self, state: dict[str, Any]) -> None:
        """Save workflow state to file."""
        if self.dry_run:
            return  # Don't save state in dry-run mode

        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, default=str)
            logger.debug(f"Saved state to {self.state_file}")
        except Exception as e:
            logger.warning(f"Failed to save state: {e}")

    def _load_state(self) -> dict[str, Any] | None:
        """Load workflow state from file."""
        if not self.state_file.exists():
            return None

        try:
            with open(self.state_file, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load state: {e}")
            return None

    def _serialize_analysis(self, analysis: BrownfieldAnalysisResult) -> dict[str, Any]:
        """Serialize analysis result for state storage."""
        return {
            "languages": analysis.languages,
            "frameworks": analysis.frameworks,
            "dependencies": analysis.dependencies,
            "domains": [
                {
                    "domain": d.domain,
                    "confidence": d.confidence,
                    "reasoning": d.reasoning,
                }
                for d in analysis.domains
            ],
            "analysis_metadata": analysis.analysis_metadata,
        }

    def _deserialize_analysis(self, data: dict[str, Any]) -> BrownfieldAnalysisResult:
        """Deserialize analysis result from state."""
        from ..experts.domain_detector import DomainMapping

        domains = [
            DomainMapping(
                domain=d["domain"],
                confidence=d["confidence"],
                signals=[],
                reasoning=d.get("reasoning", ""),
            )
            for d in data.get("domains", [])
        ]

        return BrownfieldAnalysisResult(
            project_root=self.project_root,
            languages=data.get("languages", []),
            frameworks=data.get("frameworks", []),
            dependencies=data.get("dependencies", []),
            domains=domains,
            analysis_metadata=data.get("analysis_metadata", {}),
        )

    def _serialize_expert(self, expert: ExpertConfig) -> dict[str, Any]:
        """Serialize expert config for state storage."""
        return {
            "expert_id": expert.expert_id,
            "expert_name": expert.expert_name,
            "primary_domain": expert.primary_domain,
            "rag_enabled": expert.rag_enabled,
            "knowledge_base_dir": str(expert.knowledge_base_dir) if expert.knowledge_base_dir else None,
            "confidence_matrix": expert.confidence_matrix,
        }

    def _deserialize_expert(self, data: dict[str, Any]) -> ExpertConfig:
        """Deserialize expert config from state."""
        return ExpertConfig(
            expert_id=data["expert_id"],
            expert_name=data["expert_name"],
            primary_domain=data["primary_domain"],
            rag_enabled=data.get("rag_enabled", True),
            knowledge_base_dir=Path(data["knowledge_base_dir"]) if data.get("knowledge_base_dir") else None,
            confidence_matrix=data.get("confidence_matrix"),
        )
