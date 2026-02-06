from ai_blog.utils import slugify_topic


def test_slugify_topic():
    assert (
        slugify_topic("Best Earbuds under 5000 in India")
        == "best-earbuds-under-5000-in-india"
    )
