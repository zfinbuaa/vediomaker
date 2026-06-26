import json
import time
from openai import OpenAI
from config import LLM_BASE_URL, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS, LLM_API_KEY


class LLMClient:
    def __init__(self):
        self.client = OpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)
        self.model = LLM_MODEL

    def chat(self, system_prompt: str, user_prompt: str,
             response_format: str = None, retries: int = 3) -> str:
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
                if response_format:
                    try:
                        kwargs["response_format"] = {"type": response_format}
                        resp = self.client.chat.completions.create(**kwargs)
                    except Exception:
                        del kwargs["response_format"]
                        resp = self.client.chat.completions.create(**kwargs)
                else:
                    resp = self.client.chat.completions.create(**kwargs)

                content = resp.choices[0].message.content
                finish_reason = resp.choices[0].finish_reason

                if content and content.strip():
                    return content, finish_reason

                return content, finish_reason
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

        result, finish_reason = self.chat(system_prompt, user_prompt, response_format="json_object")

        if not result or not result.strip():
            raise RuntimeError("LLM 返回空内容")

        try:
            return json.loads(result)
        except json.JSONDecodeError:
            pass

        if finish_reason == "length":
            print(f"[LLM] JSON被截断 (max_tokens={LLM_MAX_TOKENS})，请求LLM补全...")
            cont_prompt = (
                "你之前生成了一段JSON但被截断了。请从截断点继续完成剩余的JSON，"
                "只输出剩余部分，确保最终可以拼接成合法JSON。\n"
                f"已生成的部分末尾：\n{result[-300:]}"
            )
            cont_result, _ = self.chat("你是一个JSON补全助手。只输出JSON剩余部分。", cont_prompt, response_format=None)
            result = result + cont_result

            try:
                return json.loads(result)
            except json.JSONDecodeError as e:
                print(f"[LLM] 补全后仍无法解析，原始返回前500字符:\n{result[:500]}")
                raise RuntimeError(f"LLM 返回了非JSON内容: {e}")
        else:
            print(f"[LLM] JSON解析失败(finish={finish_reason})，原始返回前500字符:\n{result[:500]}")
            raise RuntimeError("LLM 返回了非JSON内容")
