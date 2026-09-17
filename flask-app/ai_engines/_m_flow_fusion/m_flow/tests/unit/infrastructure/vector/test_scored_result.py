"""
Unit tests for VectorSearchHit model (formerly VectorSearchHit) - Phase 1 verification.

Tests:
1. Backward compatibility (old code without new fields)
2. New field functionality (raw_distance, collection_name)
3. Field validation (score range, raw_distance non-negative)
4. debug_str method
"""

import pytest
from uuid import uuid4
from m_flow.adapters.vector.models import VectorSearchHit


class TestBackwardAlias:
    """Ensure the VectorSearchHit alias still resolves to VectorSearchHit."""

    def test_alias_is_same_class(self):
        assert VectorSearchHit is VectorSearchHit


class TestVectorSearchHitBackwardCompatibility:
    """Tests for backward compatibility with existing code."""

    def test_create_without_new_fields(self):
        """Old code that doesn't provide new fields should still work."""
        result = VectorSearchHit(id=uuid4(), payload={"text": "test content"}, score=0.5)

        # Should work and new fields should be None
        assert result.raw_distance is None
        assert result.collection_name is None
        assert result.score == 0.5

    def test_payload_access(self):
        """Ensure payload is accessible as before."""
        payload = {"text": "hello", "metadata": {"key": "value"}}
        result = VectorSearchHit(id=uuid4(), payload=payload, score=0.3)

        assert result.payload["text"] == "hello"
        assert result.payload["metadata"]["key"] == "value"


class TestVectorSearchHitNewFields:
    """Tests for new raw_distance and collection_name fields."""

    def test_with_new_fields(self):
        """Test creating VectorSearchHit with all new fields."""
        result = VectorSearchHit(
            id=uuid4(),
            payload={"text": "test"},
            score=0.3,
            raw_distance=0.45,
            collection_name="FacetPoint_search_text",
        )

        assert result.raw_distance == 0.45
        assert result.collection_name == "FacetPoint_search_text"
        assert result.score == 0.3

    def test_raw_distance_zero(self):
        """Test that raw_distance can be 0 (perfect match)."""
        result = VectorSearchHit(id=uuid4(), payload={}, score=0.0, raw_distance=0.0, collection_name="test")

        assert result.raw_distance == 0.0

    def test_raw_distance_large(self):
        """Test that raw_distance can be large values."""
        result = VectorSearchHit(id=uuid4(), payload={}, score=1.0, raw_distance=2.5, collection_name="Episode_summary")

        assert result.raw_distance == 2.5


class TestVectorSearchHitValidation:
    """Tests for field validation."""

    def test_score_must_be_in_range(self):
        """Score must be between 0 and 1."""
        # Valid scores
        VectorSearchHit(id=uuid4(), payload={}, score=0.0)
        VectorSearchHit(id=uuid4(), payload={}, score=0.5)
        VectorSearchHit(id=uuid4(), payload={}, score=1.0)

        # Invalid scores
        with pytest.raises(ValueError):
            VectorSearchHit(id=uuid4(), payload={}, score=-0.1)

        with pytest.raises(ValueError):
            VectorSearchHit(id=uuid4(), payload={}, score=1.5)

    def test_raw_distance_must_be_non_negative(self):
        """raw_distance must be non-negative if provided."""
        # Valid: None
        r1 = VectorSearchHit(id=uuid4(), payload={}, score=0.5, raw_distance=None)
        assert r1.raw_distance is None

        # Valid: 0
        r2 = VectorSearchHit(id=uuid4(), payload={}, score=0.5, raw_distance=0.0)
        assert r2.raw_distance == 0.0

        # Valid: positive
        r3 = VectorSearchHit(id=uuid4(), payload={}, score=0.5, raw_distance=1.5)
        assert r3.raw_distance == 1.5

        # Invalid: negative
        with pytest.raises(ValueError):
            VectorSearchHit(id=uuid4(), payload={}, score=0.5, raw_distance=-0.1)


class TestVectorSearchHitDebugStr:
    """Tests for debug_str method."""

    def test_debug_str_format(self):
        """Test debug_str returns expected format."""
        result = VectorSearchHit(
            id=uuid4(), payload={}, score=0.3, raw_distance=0.45, collection_name="test_collection"
        )

        debug = result.debug_str()

        # Should contain key information
        assert "VectorSearchHit" in debug
        assert "0.3000" in debug  # score formatted to 4 decimals
        assert "0.45" in debug
        assert "test_collection" in debug

    def test_debug_str_with_none_values(self):
        """Test debug_str handles None values gracefully."""
        result = VectorSearchHit(id=uuid4(), payload={}, score=0.5)

        debug = result.debug_str()

        assert "None" in debug
        assert "0.5000" in debug


class TestVectorSearchHitGapCalculation:
    """Tests for gap calculation scenario (simulating adaptive scoring)."""

    def test_gap_between_results(self):
        """Simulate calculating gap between top results."""
        results = [
            VectorSearchHit(id=uuid4(), payload={}, score=0.0, raw_distance=0.35, collection_name="test"),
            VectorSearchHit(id=uuid4(), payload={}, score=0.5, raw_distance=0.52, collection_name="test"),
            VectorSearchHit(id=uuid4(), payload={}, score=1.0, raw_distance=0.80, collection_name="test"),
        ]

        # Simulate gap calculation
        top1_raw = results[0].raw_distance
        top2_raw = results[1].raw_distance
        gap = max(0.0, top2_raw - top1_raw)

        assert gap == pytest.approx(0.17, rel=0.01)

    def test_single_result_gap(self):
        """When there's only one result, gap should be 0."""
        results = [
            VectorSearchHit(id=uuid4(), payload={}, score=0.0, raw_distance=0.35, collection_name="test"),
        ]

        # Simulate gap calculation with single result
        if len(results) >= 2:
            gap = results[1].raw_distance - results[0].raw_distance
        else:
            gap = 0.0

        assert gap == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
