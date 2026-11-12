import json,re,unittest
from pathlib import Path
from scripts.localize_maps import ROOT,localize,image_filename
class LocalizationTest(unittest.TestCase):
    def test_names_paths_and_idempotence(self):
        data=json.loads((ROOT/'data/acts_data.json').read_text())
        before=json.dumps(data,ensure_ascii=False)
        self.assertEqual(len(data['zones']),158)
        images=[im for z in data['zones'] for im in z['map_images']]
        self.assertEqual(len(images),537)
        self.assertEqual(len({im['src'] for im in images}),537)
        for z in data['zones']:
            self.assertRegex(z['zone_name'],r'[\u4e00-\u9fff]')
            for im in z['map_images']:
                self.assertIn(z['zone_name'],im['caption'])
                self.assertRegex(Path(im['src']).name,r'[\u4e00-\u9fff]')
                self.assertTrue((ROOT/im['src']).is_file())
                self.assertNotRegex(Path(im['src']).name,r'[<>:"/\\|?*]')
        self.assertEqual(json.dumps(localize(data),ensure_ascii=False),before)
    def test_windows_filename(self):
        self.assertEqual(image_filename('罪孽之殿：第 1 層',1,'1234567890abcdef','.png'),'罪孽之殿：第 1 層_參考圖01_1234567890abcdef.png')
