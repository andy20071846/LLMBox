from logging import getLogger

from ..metric import Gaokao_bench_metric
from .enum import GAOKAO_CHINESE_TASKS_SCORE, GAOKAO_ENGLISH_TASKS_SCORE, GAOKAO_PROMPTS, GAOKAO_TASKS
from .generation_dataset import GenerationDataset

logger = getLogger(__name__)

import re


class Gaokao(GenerationDataset):
    """The dataset of GAOKAO-Bench.

    Evaluating the Performance of Large Language Models on GAOKAO Benchmark by Xiaotian Zhang and Chunyang Li and Yi Zong and Zhengyu Ying and Liang He and Xipeng Qiu.

    Example:
        "year": "2010",
        "category": "（新课标Ⅰ）",
        "question": "21. --- Have  you finished  reading  Jane  Eyre ? \n--- No, I        my homework  all day yesterday . \nA. was doing  B. would  do C. had done  D. do\n",
        "answer": ["A"],
        "analysis": "【解答】 答案 A． was/were  doing，表示过去的某个时间点或时间段正在做某事\n，根据句意，我没有读完简爱，我昨天一天一直在写家庭作业． 故选 A． \n【点评】\n",
        "index": 0,
        "score": 1
    """

    instruction = "{}"
    example_set = None
    evaluation_set = "test"
    load_args = ("RUCAIBox/gaokao-bench",)
    metrics = [Gaokao_bench_metric()]
    categorized_subsets = None  # weighted average score

    def init_arguments(self):
        self.instruction = self.instruction.format(GAOKAO_PROMPTS[self.subset_name])
        self.extra_model_args = dict(temperature=0.3, max_tokens=4096)
        # According to https://github.com/OpenLMLab/GAOKAO-Bench/blob/main/Models/openai_gpt4.py
        # We use temperature=0.3 and max_tokens=4096

    def format_instance(self, instance):
        target = instance["answer"].__str__()
        return dict(source=instance["question"].strip(), target=" " + target)

    def post_processing(self, predictions):
        new_predictions = []
        for pred, instance in zip(predictions, self.evaluation_data):
            eval_type = GAOKAO_TASKS[self.subset_name]
            expect = len(instance["answer"])
            new_pred = self.extract_choice_answer(pred, eval_type, expect)
            new_predictions.append(tuple(new_pred) if len(new_pred) != 0 else "")
        return new_predictions

    @staticmethod
    def extract_choice_answer(model_output, question_type, answer_lenth=None):
        """
        Extract choice answer from model output

        Format of model_output that is expected:
        `'single_answer_mcq'`: Multiple-choice question (单选题). choice answer should be the last Capital Letter of the model_output, e.g.: `"...【答案】 A <eoa>"`
        `'multi_mcqs'`: Answer multiple related questions after a context, e.g. reading comprehension or cloze. `"...【答案】A ... 【答案】C ..."` or write the choice answers at the beginning of the model_output, e.g. `"A C D E F...."`
        `'multi_answers_mcq'`: Multiple-choice question, there may be more than one correct answer (多选题). `"...【答案】 ABD "` or write the choice answers at the end of the model_output, e.g. `"... ACD"`
        `'seven_option'`: Seven options for five blanks (七选五). choice answers should be the first five Capital Letters of the model_output, e.g. `"A C D F B ...."`

        sources: https://github.com/OpenLMLab/GAOKAO-Bench/blob/main/Bench/bench_function.py
        """
        if question_type == 'single_answer_mcq':
            model_answer = []
            temp = re.findall(r'[A-D](?!})', model_output[::-1])
            if len(temp) != 0:
                model_answer.append(temp[0])

        elif question_type == 'multi_mcqs':
            model_answer = []
            temp = re.findall(r"【答案】\s*[:：]*\s*[A-Z](?!})", model_output)

            if len(temp) == answer_lenth:
                for t in temp:
                    model_answer.append(re.findall(r'[A-Z](?!})', t)[0])
            else:
                temp = re.findall(r"[A-Z](?!})", model_output)
                if len(temp) > 0:
                    for k in range(min(len(temp), answer_lenth)):
                        model_answer.append(temp[k])

        elif question_type == 'multi_answers_mcq':
            model_answer = []
            answer = ''
            content = re.sub(r'\s+', '', model_output)
            answer_index = content.find('【答案】')
            if answer_index > 0:
                temp = content[answer_index:]
                if len(re.findall(r'[A-D](?!})', temp)) > 0:
                    for t in re.findall(r'[A-D](?!})', temp):
                        answer += t
            else:
                temp = content[-10:]
                if len(re.findall(r'[A-D](?!})', temp)) > 0:
                    for t in re.findall(r'[A-D](?!})', temp):
                        answer += t
            if len(answer) != 0:
                model_answer.append(answer)

        elif question_type == 'seven_option':
            model_answer = []
            temp = re.findall(r'[A-G](?!})', model_output)
            if len(temp) > 0:
                for k in range(min(5, len(temp))):
                    model_answer.append(temp[k])

        return model_answer

    @property
    def references(self):
        references = []
        for instance in self.evaluation_data:
            references.append([{
                "answer": instance["answer"],
                "task": GAOKAO_TASKS[self.subset_name],
                "score": instance["score"]
            }])
        return references
