import cv2
from collections import Counter
from deepface import DeepFace

def analyze_emotions(frame):
    try:
        analysis = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
        if isinstance(analysis, list) and len(analysis) > 0 and 'dominant_emotion' in analysis[0]:
            return analysis[0]['dominant_emotion']
        else:
            return None
    except Exception as e:
        print(f"Emotion analysis error: {e}")
        return None

def run_emotion_capture(question_text):
    cap = cv2.VideoCapture(0)
    emotion_counts = []
    face_detected = True

    print(f"\nRecording emotions for question: {question_text}")
    print("Press 'q' to stop recording...")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        emotion = analyze_emotions(frame)

        if emotion:
            if not face_detected:
                print("Face detected")
            face_detected = True
            emotion_counts.append(emotion)
            cv2.putText(frame, f"Emotion: {emotion}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        else:
            if face_detected:
                print("Face not detected")
                face_detected = False

        cv2.imshow('Emotion Capture', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    return calculate_emotion_percentages(question_text, emotion_counts)

def calculate_emotion_percentages(question_text, emotion_list):
    if not emotion_list:
        return {question_text: {}}

    total = len(emotion_list)
    counts = Counter(emotion_list)
    emotion_percentages = {emotion: round((count / total) * 100, 2) for emotion, count in counts.items()}

    return {question_text: emotion_percentages}


