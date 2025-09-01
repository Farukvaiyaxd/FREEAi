import google.generativeai as genai
import PIL.Image

# --- কোন মডেল ব্যবহার করবেন সেট করুন ---
MODEL_NAME = "gemini-1.5-pro-latest"

try:
    # ✅ আপনার API Key সরাসরি বসানো হলো
    api_key = "AIzaSyBZel0XRzlZikzX_HwfueD7jvUFmT3oeUw"
    genai.configure(api_key=api_key)

    # মডেল ইনিশিয়ালাইজ
    vision_model = genai.GenerativeModel(MODEL_NAME)
    print(f"✅ '{MODEL_NAME}' মডেল সফলভাবে লোড হয়েছে।")
    print("-" * 40)

    # ছবিটি লোড করুন
    image_path = "my-image.jpg"   # <-- আপনার ছবির নাম দিন
    img = PIL.Image.open(image_path)

    # টেক্সট প্রম্পট
    prompt_text = "এই ছবিতে কী কী দেখা যাচ্ছে? বিস্তারিত বর্ণনা দাও।"
    
    print("⏳ ছবিটি বিশ্লেষণ করা হচ্ছে...")
    response = vision_model.generate_content([prompt_text, img])

    print("\n✅ --- Vision মডেলের উত্তর ---")
    print(response.text)
    print("-" * 40)

except FileNotFoundError:
    print(f"❌ সমস্যা: '{image_path}' ছবিটি খুঁজে পাওয়া যায়নি। ফাইলটি ফোল্ডারে আছে কিনা দেখুন।")
except Exception as e:
    print(f"❌ অপ্রত্যাশিত সমস্যা হয়েছে: {e}")
