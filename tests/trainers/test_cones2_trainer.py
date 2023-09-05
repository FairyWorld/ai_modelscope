import os
import shutil
import tempfile
import unittest

from modelscope.metainfo import Trainers
from modelscope.msdatasets import MsDataset
from modelscope.pipelines import pipeline
from modelscope.trainers import build_trainer
from modelscope.utils.constant import DownloadMode
from modelscope.utils.test_utils import test_level


class TestConesDiffusionTrainer(unittest.TestCase):

    def setUp(self):
        print(('Testing %s.%s' % (type(self).__name__, self._testMethodName)))

        self.train_dataset = MsDataset.load(
            'buptwq/lora-stable-diffusion-finetune',
            split='train',
            download_mode=DownloadMode.FORCE_REDOWNLOAD)
        self.eval_dataset = MsDataset.load(
            'buptwq/lora-stable-diffusion-finetune',
            split='validation',
            download_mode=DownloadMode.FORCE_REDOWNLOAD)

        self.max_epochs = 5

        self.tmp_dir = tempfile.TemporaryDirectory().name
        if not os.path.exists(self.tmp_dir):
            os.makedirs(self.tmp_dir)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)
        super().tearDown()

    @unittest.skipUnless(test_level() >= 1, 'skip test in current test level')
    def test_cones2_diffusion_train(self):
        model_id = 'damo/Cones2'
        model_revision = 'v1.0.1'

        def cfg_modify_fn(cfg):
            cfg.train.max_epochs = self.max_epochs
            cfg.train.lr_scheduler = {
                'type': 'LambdaLR',
                'lr_lambda': lambda _: 1,
                'last_epoch': -1
            }
            cfg.train.optimizer.lr = 5e-6
            return cfg

        kwargs = dict(
            model=model_id,
            model_revision=model_revision,
            work_dir=self.tmp_dir,
            train_dataset=self.train_dataset,
            eval_dataset=self.eval_dataset,
            cfg_modify_fn=cfg_modify_fn)

        trainer = build_trainer(
            name=Trainers.cones2_inference, default_args=kwargs)
        trainer.train()
        result = trainer.evaluate()
        print(f'Cones-diffusion train output: {result}.')

        results_files = os.listdir(self.tmp_dir)
        self.assertIn(f'{trainer.timestamp}.log.json', results_files)

        pipe = pipeline(
            task=Tasks.text_to_image_synthesis, model=f'{self.tmp_dir}/output')
        output = pipe({
            'text': 'a mug and a dog on the beach',
            'subject_list': [['mug', 2], ['dog', 5]],
            'color_context': {
                '255,192,0': ['mug', 2.5],
                '255,0,0': ['dog', 2.5]
            },
            'layout': 'data/test/images/mask_example.png'
        })
        cv2.imwrite('./cones.png', output['output_imgs'][0])

    @unittest.skipUnless(test_level() >= 1, 'skip test in current test level')
    def test_cones2_diffusion_eval(self):
        model_id = 'damo/Cones2'
        model_revision = 'v1.0.1'

        kwargs = dict(
            model=model_id,
            model_revision=model_revision,
            work_dir=self.tmp_dir,
            train_dataset=None,
            eval_dataset=self.eval_dataset)

        trainer = build_trainer(
            name=Trainers.cones2_inference, default_args=kwargs)
        result = trainer.evaluate()
        print(f'Cones-diffusion eval output: {result}.')


if __name__ == '__main__':
    unittest.main()
