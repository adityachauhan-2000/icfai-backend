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

    async def create_realtime_session(self, instructions: str = None, voice: str = "ash", turn_detection: dict = None) -> Dict[str, Any]:
        """
        Create a WebRTC session using KiteFishAI /v1/realtime/session.
        """
        url = f"{self.base_url}/realtime/session"
        body = {
            "model": "kitefish-realtime",
            "voice": voice,
        }
        if instructions:
            body["instructions"] = instructions
        if turn_detection:
            body["turn_detection"] = turn_detection
        
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
                # Turn detection: use server_vad with longer silence so AI waits
                # for the candidate to fully finish speaking before responding.
                turn_detection = {
                    "type": "server_vad",
                    "threshold": 0.6,
                    "prefix_padding_ms": 400,
                    "silence_duration_ms": 1200,
                }

                if round_type == "gd":
                    instructions = (
                        f"You are Rex, a senior GD Moderator at a Fortune 500 company. "
                        f"You are moderating a group discussion for {current_student.name} "
                        f"who is from a {program_name} program background. "
                        "BEHAVIOR RULES:\n"
                        "- Begin by warmly but professionally welcoming the candidate by name, briefly introducing yourself as Rex the moderator, and then clearly stating the discussion topic.\n"
                        "- Speak at a calm, measured pace — like a real human moderator would. Never rush.\n"
                        "- After asking a question or making a point, STOP and WAIT patiently for the candidate to respond. Do NOT keep talking.\n"
                        "- Listen carefully to what the candidate says. Acknowledge their points before challenging or probing deeper.\n"
                        "- Ask follow-up questions based on what they actually said, not generic pre-planned questions.\n"
                        "- Keep your responses concise (2-3 sentences max per turn). A real moderator doesn't give speeches.\n"
                        "- Be professional and direct. Challenge weak arguments respectfully.\n"
                        "- Do NOT repeat yourself or restate the question if the candidate is still speaking."
                    )
                else:
                   instructions = (
                                        f"You are Rex, a senior Hiring Manager at a Fortune 500 company in India, conducting a personal interview. "
                                        f"You are interviewing {current_student.name} for a role matching their {program_name} program background. \n\n"
                                        "CRITICAL LANGUAGE & TONE RULES:\n"
                                        "- Speak ONLY in English. Never use any other language or mixed dialects.\n"
                                        "- Adopt the tone of a professional, articulate Indian corporate leader: warm, polite, respectful, yet thorough and evaluative.\n"
                                        "- Speak at a calm, deliberate, and relaxed pace. Use phrasing like 'Take your time,' 'That is quite interesting,' or 'I appreciate you sharing that.'\n"
                                        "- Use frequent commas, hyphens, and ellipses (...) in your responses. This naturally forces the voice engine to pause and speak more slowly.\n\n"
                                        "BEHAVIOR & TURN-TAKING RULES:\n"
                                        "- The opening: Warmly greet the candidate by name. Introduce yourself as Rex, the hiring manager. Ask a brief, welcoming question to settle them in (e.g., 'Hello {current_student.name}, it is a pleasure to meet you today... How are you doing?') and STOP.\n"
                                        "- ONE question per turn: Never ask multiple questions at once. Ask your question clearly, then STOP completely and wait for the full response.\n"
                                        "- Patient listening: Assume the candidate may pause for a few seconds while thinking. Do not rush the conversation.\n"
                                        "- Active listening: Briefly acknowledge what they just said with natural transition phrases (e.g., 'I see...', 'That makes sense...', 'Right, that is a great point...') before moving to your next question.\n"
                                        "- Deep probing: Ask tailored follow-up questions based on the details they provide, rather than reading from a generic script.\n"
                                        "- Keep turns SHORT: Limit your responses to 1 to 3 spoken sentences maximum. Real interviewers do not give monologues.\n"
                                        "- Clarification: If an answer is too brief or unclear, politely ask them to elaborate (e.g., 'Could you shed some more light on how you handled that specific challenge?')."
                                )
                
                data = await kitefish_service.create_realtime_session(
                    instructions=instructions,
                    voice="sage",
                    turn_detection=turn_detection,
                )
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
