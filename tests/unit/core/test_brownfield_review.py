"""
Unit tests for BrownfieldReviewOrchestrator
"""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from tapps_agents.core.brownfield_analyzer import BrownfieldAnalysisResult
from tapps_agents.core.brownfield_review import (
    BrownfieldReviewOrchestrator,
    BrownfieldReviewResult,
)
from tapps_agents.core.expert_config_generator import ExpertConfig
from tapps_agents.experts.knowledge_ingestion import IngestionResult


@pytest.fixture
def sample_project_root(tmp_path: Path) -> Path:
    """Create a sample project structure."""
    (tmp_path / "requirements.txt").write_text("fastapi\npytest")
    (tmp_path / ".tapps-agents").mkdir()
    return tmp_path


@pytest.fixture
def mock_context7_helper():
    """Create a mock Context7AgentHelper."""
    return Mock()


@pytest.fixture
def sample_analysis_result(sample_project_root):
    """Create a sample analysis result."""
    from tapps_agents.experts.domain_detector import DomainMapping
    
    return BrownfieldAnalysisResult(
        project_root=sample_project_root,
        languages=["python"],
        frameworks=["fastapi"],
        dependencies=["fastapi", "pytest"],
        domains=[
            DomainMapping(
                domain="python",
                confidence=0.9,
                signals=[],
                reasoning="Detected via dependency signals"
            ),
        ],
        analysis_metadata={
            "primary_language": "python",
            "primary_framework": "fastapi",
        },
    )


class TestBrownfieldReviewOrchestrator:
    """Test cases for BrownfieldReviewOrchestrator"""

    def test_init(self, sample_project_root, mock_context7_helper):
        """Test orchestrator initialization."""
        orchestrator = BrownfieldReviewOrchestrator(
            project_root=sample_project_root,
            context7_helper=mock_context7_helper,
            dry_run=False,
        )
        assert orchestrator.project_root == sample_project_root.resolve()
        assert orchestrator.context7_helper == mock_context7_helper
        assert orchestrator.dry_run is False

    def test_init_dry_run(self, sample_project_root):
        """Test orchestrator initialization with dry_run."""
        orchestrator = BrownfieldReviewOrchestrator(
            project_root=sample_project_root,
            dry_run=True,
        )
        assert orchestrator.dry_run is True

    @pytest.mark.asyncio
    async def test_review_complete(self, sample_project_root, mock_context7_helper, sample_analysis_result):
        """Test complete review workflow."""
        orchestrator = BrownfieldReviewOrchestrator(
            project_root=sample_project_root,
            context7_helper=mock_context7_helper,
            dry_run=False,
        )
        
        # Mock the internal methods
        orchestrator._analyze_codebase = AsyncMock(return_value=sample_analysis_result)
        orchestrator._create_experts = AsyncMock(return_value=[
            ExpertConfig(
                expert_id="expert-python",
                expert_name="Python Expert",
                primary_domain="python",
                rag_enabled=True,
            )
        ])
        orchestrator._populate_rag = AsyncMock(return_value={
            "expert-python": IngestionResult(
                source_type="project",
                entries_ingested=10,
                entries_failed=0,
            )
        })
        
        result = await orchestrator.review(auto=True, include_context7=True)
        
        assert isinstance(result, BrownfieldReviewResult)
        assert result.analysis == sample_analysis_result
        assert len(result.experts_created) == 1
        assert len(result.rag_results) == 1
        assert result.dry_run is False
        assert len(result.report) > 0

    @pytest.mark.asyncio
    async def test_review_dry_run(self, sample_project_root, sample_analysis_result):
        """Test review in dry-run mode."""
        orchestrator = BrownfieldReviewOrchestrator(
            project_root=sample_project_root,
            dry_run=True,
        )
        
        orchestrator._analyze_codebase = AsyncMock(return_value=sample_analysis_result)
        orchestrator._create_experts = AsyncMock(return_value=[])
        orchestrator._populate_rag = AsyncMock(return_value={})
        
        result = await orchestrator.review(auto=True, include_context7=False)
        
        assert result.dry_run is True
        assert "DRY RUN" in result.report.upper()

    @pytest.mark.asyncio
    async def test_review_without_context7(self, sample_project_root, sample_analysis_result):
        """Test review without Context7 helper."""
        orchestrator = BrownfieldReviewOrchestrator(
            project_root=sample_project_root,
            context7_helper=None,
            dry_run=False,
        )
        
        orchestrator._analyze_codebase = AsyncMock(return_value=sample_analysis_result)
        orchestrator._create_experts = AsyncMock(return_value=[])
        orchestrator._populate_rag = AsyncMock(return_value={})
        
        result = await orchestrator.review(auto=True, include_context7=False)
        
        assert isinstance(result, BrownfieldReviewResult)
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_review_error_handling(self, sample_project_root):
        """Test error handling during review."""
        orchestrator = BrownfieldReviewOrchestrator(
            project_root=sample_project_root,
            dry_run=False,
        )
        
        # Mock to raise exception
        orchestrator._analyze_codebase = AsyncMock(side_effect=Exception("Analysis failed"))
        
        result = await orchestrator.review(auto=True, include_context7=False)
        
        assert len(result.errors) > 0
        assert "Analysis failed" in result.errors[0] or "failed" in result.errors[0].lower()

    @pytest.mark.asyncio
    async def test_analyze_codebase(self, sample_project_root, sample_analysis_result):
        """Test codebase analysis step."""
        orchestrator = BrownfieldReviewOrchestrator(
            project_root=sample_project_root,
            dry_run=False,
        )
        
        # Mock analyzer
        orchestrator.analyzer.analyze = AsyncMock(return_value=sample_analysis_result)
        
        result = await orchestrator._analyze_codebase()
        
        assert result == sample_analysis_result

    @pytest.mark.asyncio
    async def test_create_experts(self, sample_project_root):
        """Test expert creation step."""
        from tapps_agents.experts.domain_detector import DomainMapping
        
        orchestrator = BrownfieldReviewOrchestrator(
            project_root=sample_project_root,
            dry_run=False,
        )
        
        domains = [
            DomainMapping(
                domain="python",
                confidence=0.9,
                signals=[],
                reasoning="Detected"
            ),
        ]
        
        # Mock config generator
        with patch.object(orchestrator.config_generator, 'generate_expert_configs') as mock_gen:
            mock_gen.return_value = [
                ExpertConfig(
                    expert_id="expert-python",
                    expert_name="Python Expert",
                    primary_domain="python",
                    rag_enabled=True,
                )
            ]
            with patch.object(orchestrator.config_generator, 'write_expert_configs') as mock_write:
                result = await orchestrator._create_experts(domains)
                
                assert len(result) == 1
                assert result[0].expert_id == "expert-python"
                mock_write.assert_called_once()

    @pytest.mark.asyncio
    async def test_populate_rag(self, sample_project_root):
        """Test RAG population step."""
        orchestrator = BrownfieldReviewOrchestrator(
            project_root=sample_project_root,
            dry_run=False,
        )
        
        experts = [
            ExpertConfig(
                expert_id="expert-python",
                expert_name="Python Expert",
                primary_domain="python",
                rag_enabled=True,
            )
        ]
        
        # Mock ingestion pipeline
        orchestrator.ingestion_pipeline.ingest_project_sources = Mock(return_value=IngestionResult(
            source_type="project",
            entries_ingested=10,
            entries_failed=0,
        ))
        
        result = await orchestrator._populate_rag(experts, include_context7=False)
        
        assert len(result) == 1
        assert "expert-python" in result
        assert result["expert-python"].entries_ingested == 10

    def test_generate_report(self, sample_project_root, sample_analysis_result):
        """Test report generation."""
        orchestrator = BrownfieldReviewOrchestrator(
            project_root=sample_project_root,
            dry_run=False,
        )
        
        result = BrownfieldReviewResult(
            analysis=sample_analysis_result,
            experts_created=[
                ExpertConfig(
                    expert_id="expert-python",
                    expert_name="Python Expert",
                    primary_domain="python",
                    rag_enabled=True,
                )
            ],
            rag_results={
                "expert-python": IngestionResult(
                    source_type="project",
                    entries_ingested=10,
                    entries_failed=0,
                )
            },
            errors=[],
            warnings=[],
            execution_time=5.0,
            dry_run=False,
        )
        
        report = orchestrator._generate_report(result)
        
        assert isinstance(report, str)
        assert "Brownfield System Review Report" in report
        assert "expert-python" in report
        assert "Python Expert" in report
        assert "10" in report  # entries ingested
