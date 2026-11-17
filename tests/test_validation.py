import pytest
from pydantic import ValidationError
from app.schemas import PostingRequest, extract_and_validate_urls


def test_valid_message_single_url():
    valid_text = "Check out our latest business platform and grow your online visibility. https://example.com"
    req = PostingRequest(message=valid_text)
    assert req.message == valid_text


def test_valid_message_with_subdomain_and_path():
    valid_text = "Discover AI tools on https://sub.dxora.io/services/v1?ref=test today!"
    req = PostingRequest(message=valid_text)
    assert "https://sub.dxora.io/services/v1?ref=test" in req.message


def test_message_exceeding_200_chars():
    long_text = "A" * 190 + " https://example.com"  # Total 210 chars > 200
    assert len(long_text) > 200
    with pytest.raises(ValidationError) as exc:
        PostingRequest(message=long_text)
    assert "exceeds the maximum limit of 200 characters" in str(exc.value)


def test_message_with_zero_urls():
    text_without_link = "Check out our latest business platform and grow your online visibility."
    with pytest.raises(ValidationError) as exc:
        PostingRequest(message=text_without_link)
    assert "Message must contain exactly one Call-To-Action (CTA) link, but none was found" in str(exc.value)


def test_message_with_multiple_urls():
    text_with_two_links = "Visit https://example.com or visit https://dxora.com for info."
    with pytest.raises(ValidationError) as exc:
        PostingRequest(message=text_with_two_links)
    assert "Message must contain exactly one Call-To-Action (CTA) link, but 2 were found" in str(exc.value)


def test_empty_message():
    with pytest.raises(ValidationError) as exc:
        PostingRequest(message="   ")
    assert "cannot be empty" in str(exc.value)


def test_invalid_url_scheme():
    with pytest.raises(ValueError) as exc:
        extract_and_validate_urls("Check ftp://example.com/files")
    # Scheme ftp is not matched by URL_REGEX or rejected
    assert "Call-To-Action (CTA) link" in str(exc.value) or "scheme" in str(exc.value)


def test_invalid_domain_structure():
    with pytest.raises(ValueError) as exc:
        extract_and_validate_urls("Check https://invalid_domain_without_tld/path")
    assert "Call-To-Action (CTA) link" in str(exc.value) or "domain" in str(exc.value)
