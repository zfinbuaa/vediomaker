import json
from openai import OpenAI
from config import LLM_BASE_URL, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS, LLM_API_KEY


class LLMClient:
    def __init__(self):
        self.client = OpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)
        self.model = LLM_MODEL

    def chat(self, system_prompt: str, user_prompt: str, response_format: str = "json_object") -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
            response_format={"type": response_format},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return resp.choices[0].message.content

    def generate_segments(self, doc_content: str) -> dict:
        system_prompt = (
            "你是一个视频文案生成器。根据用户提供的文档/README内容，生成一个教学演示视频的分段脚本。\n"
            "要求：\n"
            "- 将内容拆分为多个独立的段落(segment)，每个段落是一个独立的讲解单元\n"
            "- 每个段落包含一段旁白文本(text)，字数适中，适合口语朗读\n"
            "- 给出每段旁白的预估朗读时长(duration_seconds，中文按每秒3-4字估算)\n"
            "- 每个段落的text应该自然流畅、独立完整\n"
            "- 返回严格合法的JSON，格式如下：\n"
            '{"title": "视频标题", "segments": ['
            '{"id": 1, "text": "旁白文本内容", "duration_seconds": 5},'
            '{"id": 2, "text": "第二段旁白内容", "duration_seconds": 8}'
            ']}'
        )
        user_prompt = f"请根据以下文档内容生成视频分段文案：\n\n{doc_content}"
        result = self.chat(system_prompt, user_prompt)
        return json.loads(result)
