import unittest
class TemplateTestCase(unittest.TestCase):


    def test1(self):
        x = 'blee'
        self.assertEqual(x, 'blee')


if __name__ == '__main__':
    unittest.main()

