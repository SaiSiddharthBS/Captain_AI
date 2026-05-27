import os
import base64
import ollama
from PIL import ImageGrab

class VisionEngine:
    def __init__(self, model="moondream"):
        self.model = model
        self.available = True
        
        # Test if the model exists locally
        try:
            response = ollama.list()
            # Handle both old dict-based and new object-based Ollama SDK
            models = getattr(response, 'models', response.get('models', [])) if hasattr(response, 'models') else response.get('models', [])
            model_names = [getattr(m, 'model', m.get('name', '')) if hasattr(m, 'model') else m.get('name', '') for m in models]
            
            if not any(self.model in name for name in model_names):
                print(f"[VisionEngine] WARNING: Model '{self.model}' not found locally.")
                print(f"[VisionEngine] Please run: ollama pull {self.model}")
                self.available = False
        except Exception as e:
            print(f"[VisionEngine] Error connecting to Ollama: {e}")
            self.available = False

    def look_at_screen(self, prompt: str = "Describe what is on this screen briefly."):
        """Takes a screenshot and asks the vision model about it."""
        if not self.available:
            return "Vision model is not available or not installed."
            
        temp_img_path = "temp_screen.png"
        try:
            # 1. Take Screenshot
            screenshot = ImageGrab.grab()
            # Convert to RGB to drop alpha channel if present
            screenshot = screenshot.convert("RGB")
            
            # Reduce resolution to aggressively speed up local inference on 8GB models
            # 512x512 cuts the 'Time to First Token' math in half compared to 768x768
            screenshot.thumbnail((512, 512))
            
            # Save compressed image
            screenshot.save(temp_img_path)
            
            # 2. Encode Image
            with open(temp_img_path, "rb") as image_file:
                img_data = image_file.read()
                
            # 3. Send to Ollama
            response = ollama.chat(
                model=self.model,
                messages=[{
                    'role': 'user',
                    'content': prompt,
                    'images': [img_data]
                }]
            )
            
            return response['message']['content']
            
        except Exception as e:
            print(f"[VisionEngine] Error processing image: {e}")
            return "I hit an error trying to look at the screen."
        finally:
            # Cleanup
            if os.path.exists(temp_img_path):
                os.remove(temp_img_path)

    def look_at_screen_stream(self, prompt: str = "Describe what is on this screen briefly."):
        """Stream the vision model's response token-by-token."""
        if not self.available:
            yield "Vision model is not available or not installed."
            return
            
        temp_img_path = "temp_screen.png"
        try:
            screenshot = ImageGrab.grab().convert("RGB")
            screenshot.thumbnail((512, 512))
            screenshot.save(temp_img_path)
            
            with open(temp_img_path, "rb") as image_file:
                img_data = image_file.read()
                
            response = ollama.chat(
                model=self.model,
                messages=[{
                    'role': 'user',
                    'content': prompt,
                    'images': [img_data]
                }],
                stream=True
            )
            
            for chunk in response:
                yield chunk['message']['content']
                
        except Exception as e:
            print(f"[VisionEngine] Error processing image stream: {e}")
            yield "I hit an error trying to look at the screen."
        finally:
            if os.path.exists(temp_img_path):
                os.remove(temp_img_path)
