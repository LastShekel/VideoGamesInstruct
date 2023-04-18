import unittest

from main import get_html, get_html_for_reviews_page, HOST, URL


class MyTestCase(unittest.TestCase):
    def test_get_html(self):
        res = get_html(HOST)
        self.assertIsNotNone(res)

    def test_get_html_for_reviews_page(self):
        res = get_html_for_reviews_page(URL, 1)
        self.assertIsNotNone(res)


if __name__ == '__main__':
    unittest.main()
