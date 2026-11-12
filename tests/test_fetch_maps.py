import unittest
from scripts.fetch_maps import Article
class ParserTest(unittest.TestCase):
    def test_only_document_content_and_images(self):
        parser=Article()
        parser.feed('''<article><nav><li>Breadcrumb</li><img src="logo.png"></nav>
        <div class="theme-doc-markdown markdown"><h1>Coast</h1><h2>Layouts</h2>
        <p>Follow the <strong>coast</strong>.</p><img src="/assets/map.png" alt="Variant 1">
        </div></article><footer><p>Ignore footer</p></footer>''')
        self.assertEqual(parser.title,'Coast')
        self.assertEqual(parser.blocks,['Follow the coast.'])
        self.assertEqual(parser.images,[{'src':'/assets/map.png','caption':'Variant 1'}])
if __name__=='__main__': unittest.main()
