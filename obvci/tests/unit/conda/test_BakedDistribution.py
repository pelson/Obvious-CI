import os
import shutil
import tempfile
import unittest

from conda_build.metadata import MetaData

from obvci.conda_tools.build_directory import BakedDistribution


class Test_conditional_recipe(unittest.TestCase):
    # Tests cases where a recipe changes based on external
    # conditions, such as the definition of the PYTHON version.
    def setUp(self):
        self.recipe_dir = tempfile.mkdtemp(prefix='tmp_obvci_recipe_')

    def tearDown(self):
        shutil.rmtree(self.recipe_dir)

    def test_py_version(self):
        recipe = """
            package:
                name: recipe_which_depends_on_py_version
                version: 3  # [py3k]
                version: 2  # [not py3k]
            """.replace('\n' + ' ' * 12, '\n').strip()
        with open(os.path.join(self.recipe_dir, 'meta.yaml'), 'w') as fh:
            fh.write(recipe)
        os.environ['CONDA_PY'] = '27'
        meta = MetaData(self.recipe_dir)
        dist = BakedDistribution(meta, (('python', '27', ), ))
        self.assertEqual(dist.version(), u'2')

        dist = BakedDistribution(meta, (('python', '35', ), ))
        self.assertEqual(dist.version(), u'2')
        # When we trigger re-reading, ensure that the version is correctly
        # reflected.
        dist.parse_again()
        self.assertEqual(dist.version(), u'3')


if __name__ == '__main__':
    unittest.main()
