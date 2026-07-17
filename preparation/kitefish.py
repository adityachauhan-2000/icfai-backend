import os
import json
import requests
import asyncio
import logging
from typing import Optional, Dict, Any
from fastapi import UploadFile

logger = logging.getLogger(__name__)

class KiteFishAIService:
    def __init__(self, api_key: str = None):
        # Using hardcoded key as fallback because Vercel doesn't have access to the local .env
        self.api_key = api_key or os.getenv("KITEFISH_API_KEY", "932c84dfea66476791f94b5ee80384eb")
        self.base_url = "https://api.kitefishai.com/v1"
        self.headers = {
            "x-api-key": self.api_key
        }

    async def create_realtime_session(self, instructions: str = None) -> Dict[str, Any]:
        """
        Create a WebRTC session using KiteFishAI /v1/realtime/session.
        """
        url = f"{self.base_url}/realtime/session"
        body = {"model": "kitefish-realtime"}
        if instructions:
            body["instructions"] = instructions
        
        def make_request():
            return requests.post(url, headers=self.headers, json=body, timeout=10)
            
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(None, make_request)
        
        try:
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error("KiteFishAI create session failed: %s", str(e))
            raise e

    async def exchange_sdp(self, client_secret: str, sdp_offer: str) -> str:
        """
        Complete WebRTC handshake using KiteFishAI /v1/realtime/sdp.
        """
        url = f"{self.base_url}/realtime/sdp"
        headers = {
            "X-api-key": self.api_key,
            "Authorization": f"Bearer {client_secret}",
            "Content-Type": "application/sdp"
        }
        
        def make_request():
            return requests.post(url, headers=headers, data=sdp_offer, timeout=10)
            
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(None, make_request)
        
        try:
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            logger.error("KiteFishAI exchange SDP failed: %s", str(e))
            raise e

    async def analyze_video(self, video_file: UploadFile) -> Dict[str, Any]:
        """
        Analyze GD video for posture and seating behavior using KiteFishAI /v1/video endpoint.
        """
        url = f"{self.base_url}/video"
        
        content = await video_file.read()
        mime_type = video_file.content_type or "video/webm"
        files = {"file": (video_file.filename, content, mime_type)}
        
        prompt = "Analyze the candidate's posture, seating behavior, eye contact, and professional presence in this Group Discussion video. Give a concise summary of their visual presence."
        data = {"prompt": prompt}

        def make_request():
            return requests.post(url, headers=self.headers, files=files, data=data, timeout=180)
            
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(None, make_request)
        
        try:
            payload = resp.json()
            print("\n" + "="*40)
            print("📹 KITEFISH VIDEO ANALYSIS RAW RESPONSE:")
            print(json.dumps(payload, indent=2))
            print("="*40 + "\n")
            
            response_obj = payload.get("response") or {}
            content = response_obj.get("content") if isinstance(response_obj, dict) else payload.get("content", "No analysis")
            return {"posture_analysis": content}
        except Exception as e:
            logger.error("KiteFishAI video analysis failed: %s", str(e))
            return {"posture_analysis": "Failed to analyze video."}

    async def transcribe_audio(self, audio_file: UploadFile) -> str:
        """
        Transcribe interview audio using KiteFishAI /v1/stt.
        """
        url = f"{self.base_url}/stt"
        content = await audio_file.read()
        mime_type = audio_file.content_type or "audio/webm"
        files = {"file": (audio_file.filename, content, mime_type)}
        
        def make_request():
            return requests.post(url, headers=self.headers, files=files, timeout=180)
            
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(None, make_request)
        
        try:
            payload = resp.json()
            print("\n" + "="*40)
            print("🎙️ KITEFISH STT RAW RESPONSE:")
            print(json.dumps(payload, indent=2))
            print("="*40 + "\n")
            
            response_obj = payload.get("response") or {}
            if isinstance(response_obj, dict):
                return response_obj.get("text", "")
            return ""
        except Exception as e:
            logger.error("KiteFishAI STT failed: %s", str(e))
            return ""

    async def generate_reasoning(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        """
        Generic endpoint for generating reasoning directly for testing.
        """
        url = f"{self.base_url}/chat"
        
        body = {
            "model": "kitefish-reasoning",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        }

        def make_request():
            resp = requests.post(url, headers=self.headers, json=body)
            resp.raise_for_status()
            return resp

        loop = asyncio.get_event_loop()
        try:
            resp = await loop.run_in_executor(None, make_request)
            payload = resp.json()
            raw_content = payload.get("response", {}).get("content", "")
            
            if raw_content.find('{') != -1:
                json_str = raw_content[raw_content.find('{'):]
                if json_str.rfind('}') != -1:
                    json_str = json_str[:json_str.rfind('}')+1]
                return json.loads(json_str)
            return {"raw_response": raw_content}
        except Exception as e:
            logger.error("Generic reasoning failed: %s", str(e))
            return {"error": str(e)}

    async def generate_interview_report(self, gd_transcript: str, interview_transcript: str, posture_analysis: str, aptitude_score: dict, gd_question: str = "", interview_question: str = "") -> Dict[str, Any]:
        """
        Generate final report using KiteFishAI /v1/chat (kitefish-reasoning).
        """
        url = f"{self.base_url}/chat"
        
        system_prompt = (
            "You are an expert HR interviewer and evaluator at an enterprise-level recruiting agency. "
            "Your task is to provide an exceptionally rigorous, high-standard evaluation for a candidate broken down by round. "
            "You will be given the GD (Group Discussion) details including the question asked, Personal Interview details including the question asked, and a Video Posture Analysis. "
            "You must return an `overall_score` out of 40 points total (GD is worth 20 points, Personal Interview is worth 20 points, which includes posture/behavior evaluation). "
            "Do NOT include Aptitude in this score (it is scored out of 60 by the backend). "
            "CRITICAL SCORING RULES:\n"
            "- You MUST be extremely strict and critical. Grade like a top-tier management consultant evaluator.\n"
            "- If a candidate did not participate, provided nothing, or if transcripts/posture analysis are placeholder values indicating no attempt (e.g. containing phrases like 'No audio provided', 'No video provided', 'too short or empty', or are empty/whitespace), you MUST assign a score of 0 for that round. If they do nothing in both rounds, `overall_score` MUST be 1 or 2.\n"
            "- If the candidate's answers are minimal, very short (e.g., under 2-3 sentences), repetitive, or lack substance, assign a maximum of 1 to 3 points out of 20 for that round.\n"
            "- Actively penalize use of filler words (um, ah, like), grammatical errors, weak vocabulary, or lack of logical structure. Be highly critical of poor communication skills.\n"
            "- A score above 15 out of 20 should ONLY be given for absolutely flawless, structured, industry-expert-level responses. An average response should score no more than 8 to 10 points out of 20.\n\n"
            "Return ONLY a valid raw JSON object matching the schema below. Do not wrap it in markdown.\n\n"
            "JSON SCHEMA:\n"
            "{\n"
            "  \"overall_score\": 12,\n"
            "  \"feedback_summary\": \"Detailed, professional paragraph summarizing overall performance, strengths, and major flaws across all rounds\",\n"
            "  \"gd_feedback\": \"Detailed feedback on how the candidate addressed the specific Group Discussion topic/question.\",\n"
            "  \"interview_feedback\": \"Detailed feedback on how the candidate addressed the specific Personal Interview question.\",\n"
            "  \"improvements\": [\"highly\", \"specific\", \"actionable\", \"areas\", \"to\", \"improve\"],\n"
            "  \"posture_behavior_feedback\": \"Feedback strictly based on the provided video posture analysis, framed professionally.\",\n"
            "  \"grammar_pronunciation_notes\": \"Detailed notes on any noticeable issues with grammar, fluency, or communication from transcripts.\"\n"
            "}"
        )
        
        user_content = (
            f"Group Discussion Question Asked: {gd_question}\n"
            f"Group Discussion Transcript: {gd_transcript}\n\n"
            f"Video Posture Analysis (from Interview Video): {posture_analysis}\n\n"
            f"Personal Interview Question Asked: {interview_question}\n"
            f"Personal Interview Transcript: {interview_transcript}\n\n"
            "Evaluate the candidate strictly according to the rules and return the JSON."
        )

        body = {
            "model": "kitefish-reasoning",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
        }

        def make_request():
            return requests.post(url, headers=self.headers, json=body, timeout=180)
            
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(None, make_request)
        
        try:
            payload = resp.json()
            print("\n" + "="*40)
            print("KITEFISH REASONING RAW RESPONSE:")
            print(json.dumps(payload, indent=2))
            print("="*40 + "\n")
            
            response_obj = payload.get("response") or {}
            if isinstance(response_obj, dict):
                raw_content = response_obj.get("content", "").strip()
            else:
                raw_content = ""
            
            if raw_content.startswith("```"):
                first_nl = raw_content.find("\n")
                if first_nl != -1:
                    raw_content = raw_content[first_nl:].strip()
                if raw_content.endswith("```"):
                    raw_content = raw_content[:-3].strip()
            
            # Robust JSON parsing
            start_idx = raw_content.find('{')
            if start_idx != -1:
                raw_content = raw_content[start_idx:].strip()
                if not raw_content.endswith('}'):
                    raw_content += "\n}"
            
            return json.loads(raw_content)
        except Exception as e:
            logger.error("KiteFishAI reasoning failed: %s", str(e))
            return {
                "overall_score": 50,
                "feedback_summary": f"Analysis failed to parse. Error: {str(e)}",
                "improvements": ["Please try again."],
                "posture_behavior_feedback": "N/A",
                "grammar_pronunciation_notes": "N/A"
            }
