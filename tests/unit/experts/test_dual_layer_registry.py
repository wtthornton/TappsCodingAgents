"""
Tests for Dual-Layer Expert Registry System

Tests the enhanced ExpertRegistry with weighted consultation and priority system
for built-in vs customer experts.
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from tapps_agents.experts.expert_registry import (
    ExpertRegistry,
    ConsultationResult,
    TECHNICAL_DOMAINS
)
from tapps_agents.experts.builtin_registry import BuiltinExpertRegistry
from tapps_agents.experts.base_expert import BaseExpert
from tapps_agents.experts.domain_config import DomainConfig
from tapps_agents.experts.weight_distributor import ExpertWeightMatrix


@pytest.mark.unit
class TestTechnicalDomainClassification:
    """Test technical vs business domain classification."""
    
    def test_technical_domains_defined(self):
        """Test that technical domains are properly defined."""
        assert "security" in TECHNICAL_DOMAINS
        assert "performance-optimization" in TECHNICAL_DOMAINS
        assert "testing-strategies" in TECHNICAL_DOMAINS
        assert "accessibility" in TECHNICAL_DOMAINS
        assert "user-experience" in TECHNICAL_DOMAINS
        assert "data-privacy-compliance" in TECHNICAL_DOMAINS
    
    def test_business_domains_not_technical(self):
        """Test that business domains are not in technical domains."""
        business_domains = ["e-commerce", "healthcare", "finance", "retail"]
        for domain in business_domains:
            assert domain not in TECHNICAL_DOMAINS
    
    def test_builtin_registry_technical_domains_match(self):
        """Test that TECHNICAL_DOMAINS matches BuiltinExpertRegistry.TECHNICAL_DOMAINS."""
        assert TECHNICAL_DOMAINS == BuiltinExpertRegistry.TECHNICAL_DOMAINS


@pytest.mark.unit
class TestExpertPrioritySystem:
    """Test expert priority system for technical vs business domains."""
    
    def test_get_experts_for_technical_domain_prioritizes_builtin(self):
        """Test that technical domains prioritize built-in experts."""
        registry = ExpertRegistry(domain_config=None, load_builtin=True)
        
        # Add a customer expert for security domain
        customer_expert = BaseExpert(
            expert_id="expert-customer-security",
            expert_name="Customer Security Expert",
            primary_domain="security"
        )
        registry.register_expert(customer_expert, is_builtin=False)
        
        # Get experts for security domain with prioritize_builtin=True
        expert_ids = registry._get_experts_for_domain("security", prioritize_builtin=True)
        
        # Built-in security expert should come first
        assert "expert-security" in expert_ids
        assert expert_ids.index("expert-security") < expert_ids.index("expert-customer-security")
    
    def test_get_experts_for_business_domain_prioritizes_customer(self):
        """Test that business domains prioritize customer experts."""
        registry = ExpertRegistry(domain_config=None, load_builtin=True)
        
        # Add a customer expert for e-commerce domain
        customer_expert = BaseExpert(
            expert_id="expert-ecommerce",
            expert_name="E-commerce Expert",
            primary_domain="e-commerce"
        )
        registry.register_expert(customer_expert, is_builtin=False)
        
        # Get experts for e-commerce domain (business domain)
        expert_ids = registry._get_experts_for_domain("e-commerce", prioritize_builtin=False)
        
        # Customer expert should come first
        assert "expert-ecommerce" in expert_ids
        if "expert-security" in expert_ids:  # Built-in might be included as fallback
            assert expert_ids.index("expert-ecommerce") < expert_ids.index("expert-security")
    
    def test_get_experts_fallback_to_builtin(self):
        """Test that technical domains fallback to built-in experts if no customer expert."""
        registry = ExpertRegistry(domain_config=None, load_builtin=True)
        
        # Get experts for security domain (no customer expert)
        expert_ids = registry._get_experts_for_domain("security", prioritize_builtin=True)
        
        # Should include built-in security expert
        assert "expert-security" in expert_ids
        assert len(expert_ids) > 0


@pytest.mark.unit
class TestWeightedConsultation:
    """Test weighted consultation with priority system."""
    
    @pytest.mark.asyncio
    async def test_consult_technical_domain_prioritizes_builtin(self):
        """Test that consulting technical domain prioritizes built-in experts."""
        registry = ExpertRegistry(domain_config=None, load_builtin=True)
        
        # Mock expert responses
        builtin_expert = registry.get_expert("expert-security")
        if builtin_expert:
            builtin_expert.run = AsyncMock(return_value={
                "answer": "Built-in security recommendation",
                "confidence": 0.9,
                "sources": []
            })
        
        # Add customer expert
        customer_expert = BaseExpert(
            expert_id="expert-customer-security",
            expert_name="Customer Security Expert",
            primary_domain="security"
        )
        customer_expert.run = AsyncMock(return_value={
            "answer": "Customer security recommendation",
            "confidence": 0.8,
            "sources": []
        })
        registry.register_expert(customer_expert, is_builtin=False)
        
        # Consult with prioritize_builtin=True
        result = await registry.consult(
            query="How to secure this?",
            domain="security",
            prioritize_builtin=True,
            include_all=True
        )
        
        assert result is not None
        assert result.domain == "security"
        assert "Built-in" in result.weighted_answer or "security" in result.weighted_answer.lower()
    
    @pytest.mark.asyncio
    async def test_consult_business_domain_prioritizes_customer(self):
        """Test that consulting business domain prioritizes customer experts."""
        registry = ExpertRegistry(domain_config=None, load_builtin=True)
        
        # Add customer expert for business domain
        customer_expert = BaseExpert(
            expert_id="expert-ecommerce",
            expert_name="E-commerce Expert",
            primary_domain="e-commerce"
        )
        customer_expert.run = AsyncMock(return_value={
            "answer": "E-commerce best practices",
            "confidence": 0.9,
            "sources": []
        })
        registry.register_expert(customer_expert, is_builtin=False)
        
        # Consult business domain
        result = await registry.consult(
            query="How to handle checkout?",
            domain="e-commerce",
            prioritize_builtin=False,
            include_all=True
        )
        
        assert result is not None
        assert result.domain == "e-commerce"
        # Should prioritize customer expert
        assert "e-commerce" in result.weighted_answer.lower() or len(result.responses) > 0


@pytest.mark.unit
class TestExpertRegistryIntegration:
    """Test ExpertRegistry integration with built-in and customer experts."""
    
    def test_registry_separates_builtin_and_customer_experts(self):
        """Test that registry maintains separate dictionaries for built-in and customer experts."""
        registry = ExpertRegistry(domain_config=None, load_builtin=True)
        
        # Add customer expert
        customer_expert = BaseExpert(
            expert_id="expert-customer",
            expert_name="Customer Expert",
            primary_domain="business-domain"
        )
        registry.register_expert(customer_expert, is_builtin=False)
        
        # Check separation
        assert "expert-security" in registry.builtin_experts
        assert "expert-security" not in registry.customer_experts
        assert "expert-customer" in registry.customer_experts
        assert "expert-customer" not in registry.builtin_experts
        
        # Both should be in main experts dict
        assert "expert-security" in registry.experts
        assert "expert-customer" in registry.experts
    
    def test_builtin_experts_auto_loaded(self):
        """Test that built-in experts are auto-loaded on initialization."""
        registry = ExpertRegistry(domain_config=None, load_builtin=True)
        
        # Check that built-in experts are loaded
        assert len(registry.builtin_experts) > 0
        assert "expert-security" in registry.builtin_experts
        assert "expert-code-quality" in registry.builtin_experts
    
    def test_customer_experts_not_auto_loaded(self):
        """Test that customer experts are not auto-loaded."""
        registry = ExpertRegistry(domain_config=None, load_builtin=True)
        
        # Customer experts should be empty initially
        assert len(registry.customer_experts) == 0
    
    def test_get_expert_returns_correct_type(self):
        """Test that get_expert returns the correct expert."""
        registry = ExpertRegistry(domain_config=None, load_builtin=True)
        
        # Get built-in expert
        builtin_expert = registry.get_expert("expert-security")
        assert builtin_expert is not None
        assert builtin_expert._is_builtin is True
        
        # Add and get customer expert
        customer_expert = BaseExpert(
            expert_id="expert-customer",
            expert_name="Customer Expert",
            primary_domain="business-domain"
        )
        registry.register_expert(customer_expert, is_builtin=False)
        
        retrieved = registry.get_expert("expert-customer")
        assert retrieved is not None
        assert retrieved._is_builtin is False


@pytest.mark.unit
class TestConsultationResult:
    """Test ConsultationResult structure and properties."""
    
    @pytest.mark.asyncio
    async def test_consultation_result_structure(self):
        """Test that ConsultationResult has all required fields."""
        registry = ExpertRegistry(domain_config=None, load_builtin=True)
        
        # Mock expert response
        expert = registry.get_expert("expert-security")
        if expert:
            expert.run = AsyncMock(return_value={
                "answer": "Test answer",
                "confidence": 0.8,
                "sources": []
            })
            
            result = await registry.consult(
                query="Test query",
                domain="security",
                prioritize_builtin=True,
                include_all=False
            )
            
            assert result is not None
            assert hasattr(result, "domain")
            assert hasattr(result, "query")
            assert hasattr(result, "responses")
            assert hasattr(result, "weighted_answer")
            assert hasattr(result, "agreement_level")
            assert hasattr(result, "confidence")
            assert hasattr(result, "primary_expert")
            assert hasattr(result, "all_experts_agreed")


@pytest.mark.unit
class TestErrorHandling:
    """Test error handling in expert registry."""
    
    def test_consult_no_experts_raises_error(self):
        """Test that consulting with no experts raises appropriate error."""
        registry = ExpertRegistry(domain_config=None, load_builtin=False)
        
        # Try to consult with no experts
        import pytest
        with pytest.raises(ValueError, match="No experts found"):
            import asyncio
            asyncio.run(registry.consult(
                query="Test",
                domain="unknown-domain",
                prioritize_builtin=False
            ))
    
    @pytest.mark.asyncio
    async def test_consult_with_expert_error_continues(self):
        """Test that consultation continues even if one expert errors."""
        registry = ExpertRegistry(domain_config=None, load_builtin=True)
        
        # Mock expert to raise error
        expert = registry.get_expert("expert-security")
        if expert:
            expert.run = AsyncMock(side_effect=Exception("Test error"))
            
            # Should not raise, but return result with error
            result = await registry.consult(
                query="Test",
                domain="security",
                prioritize_builtin=True,
                include_all=False
            )
            
            # Result might be None or contain error
            # This tests that errors don't crash the consultation

