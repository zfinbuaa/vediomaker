import json
import time
from openai import OpenAI
from config import LLM_BASE_URL, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS, LLM_API_KEY


class LLMClient:
    def __init__(self):
        self.client = OpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)
        self.model = LLM_MODEL

    def chat(self, system_prompt: str, user_prompt: str,
             response_format: str = "json_object", retries: int = 3) -> str:
        last_error = None
        for attempt in range(retries):
            try:
                kwargs = {
                    "model": self.model,
                    "temperature": LLM_TEMPERATURE,
                    "max_tokens": LLM_MAX_TOKENS,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                }
                try:
                    kwargs["response_format"] = {"type": response_format}
                    resp = self.client.chat.completions.create(**kwargs)
                except Exception:
                    del kwargs["response_format"]
                    resp = self.client.chat.completions.create(**kwargs)

                content = resp.choices[0].message.content
                if content and content.strip():
                    return content
            except Exception as e:
                last_error = e
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
        raise RuntimeError(f"LLM API 调用失败 (试了 {retries} 次): {last_error}")

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

        if not result or not result.strip():
            raise RuntimeError("LLM 返回空内容")

        try:
            return json.loads(result)
        except json.JSONDecodeError as e:
            print(f"[LLM] JSON解析失败，原始返回前500字符:\n{result[:500]}")
            raise RuntimeError(f"LLM 返回了非JSON内容: {e}")
