"""Unit tests for template parsers - output."""


class TestParseOutputBasic:
    """Basic test cases for parse_output function."""

    def test_template_has_output(self):
        """Test that loaded template has output configuration."""
        from hyperextract.utils.template_engine import Gallery

        template = Gallery.get("general/model")

        assert template is not None
        assert hasattr(template, "output")

    def test_template_output_has_fields(self):
        """Test that template output has fields."""
        from hyperextract.utils.template_engine import Gallery

        template = Gallery.get("general/model")

        assert template is not None
        assert hasattr(template, "output")
        assert hasattr(template.output, "fields")


class TestParseIdentifiers:
    """Test cases for parse_identifiers function."""

    def test_template_has_identifiers(self):
        """Test that loaded template has identifiers configuration."""
        from hyperextract.utils.template_engine import Gallery

        template = Gallery.get("general/set")

        assert template is not None
        assert hasattr(template, "identifiers")
