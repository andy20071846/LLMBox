from .sftdataset import SFTDataset


class SelfInstructDataset(SFTDataset):
    """
    Self-instuct dataset is generated by GPT3 and contains 52k instructions, paired with 82K instance inputs and outputs.
    """

    instruction_template = "\n\n### Instruction:\n"
    response_template = "\n\n### Response:\n"
    format_template = {
        "prompt_input": (
            "Below is an instruction that describes a task, paired with an input that provides further context. "
            + "Write a response that appropriately completes the request."
            + instruction_template
            + "{instruction}"
            + "{input}"
            + response_template
            + "{response}"
        ),
        "prompt_no_input": (
            "Below is an instruction that describes a task. "
            + "Write a response that appropriately completes the request."
            + instruction_template
            + "{instruction}"
            + response_template
            + "{response}"
        ),
    }

    def formatting_func(self, examples):
        output_texts = []
        for instruction, input_text, response in zip(examples["instruction"], examples["input"], examples["output"]):
            if input_text:
                text = self.format_template["prompt_input"].format(
                    instruction=instruction, input=input_text, response=response
                )
            else:
                text = self.format_template["prompt_no_input"].format(instruction=instruction, response=response)
            output_texts.append(text)
        return output_texts
