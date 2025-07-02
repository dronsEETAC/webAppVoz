import cv2

# Los indices de la camara empiezan en el 0 y para salir simplemente le das a la Q

camera_index = int(input("Select camera index (0 for default): "))
cap = cv2.VideoCapture(camera_index)

if not cap.isOpened():
    print(f"Cannot open camera {camera_index}")
    exit()


while True:
    ret, frame = cap.read()
    if not ret:

        print("Failed to capture frame")
        break

    cv2.imshow(f"Camera {camera_index}", frame)


    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()