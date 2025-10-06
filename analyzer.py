frame_history = []

def analyze_videos(front_path, side_path):
    chosen_frame = None
    reset_detection_state()
    global model, pose, pose_side, prev_distance, prev_frame, skip_frames, prev_pitch, initial_detections, determined_foot, detection_count, prev_side_frame, chosen_side_frame

    cap = cv2.VideoCapture(front_path)
    cap2 = cv2.VideoCapture(side_path)
    
    results = []
    increase_count = 0  # عداد لمرات زيادة المسافة
    last_distance = None  
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break  
        ret2, side_frame = cap2.read()
        if not ret2:
            break 
            
        frame_for_headpose = frame.copy()
        processed_frame, direction, pitch, yaw, roll, bbox = detect_head_pose(frame_for_headpose)  
         
        frame, center, ball_diameter, box = detect_ball(frame)
        side_frame, center_side, side_ball_diameter, side_box = detect_ball(side_frame)
        side_frame, person_center, person_diameter, best_box = detect_person(side_frame)
           
        right_ankle, left_ankle, right_heel, left_heel, finger_xy_l, finger_xy_r, left_hip, right_hip, left_shoulder, right_shoulder, left_knee, right_knee = process_pose_and_draw_arrows(frame, pose)
        side_right_ankle, side_left_ankle, side_right_heel, side_left_heel, side_finger_xy_l, side_finger_xy_r, side_left_hip, side_right_hip, side_left_shoulder, side_right_shoulder, side_left_knee, side_right_knee = process_pose_and_draw_arrows(side_frame, pose_side)

        foot = detect_receiving_foot(best_box, center_side)
        real_distance = calculate_ankle_ball_dist_and_draw(frame, right_ankle, left_ankle, center, ball_diameter, foot)

        if skip_frames > 0:
            skip_frames -= 1
            continue

        receiving = check_receiving_position(side_frame, side_right_ankle, side_left_ankle, center_side, best_box)

        if receiving:
            if foot == "right":
                distance = math.sqrt((side_right_ankle[0] - center_side[0])**2 + (side_right_ankle[1] - center_side[1])**2)
            elif foot == "left":
                distance = math.sqrt((side_left_ankle[0] - center_side[0])**2 + (side_left_ankle[1] - center_side[1])**2)
            else:
                distance = None

            if distance is not None:
                frame_history.append({'distance': distance, 'frame': frame.copy(), 'side_frame': side_frame.copy()})
                if len(frame_history) > 3:
                    frame_history.pop(0)

                if last_distance is not None:
                    if distance > last_distance:
                        increase_count += 1
                    else:
                        increase_count = 0

                last_distance = distance

                # لو المسافة كبرت 3 مرات متتالية → نختار أصغر فريم
                if increase_count >= 3 and len(frame_history) == 3:
                    best = min(frame_history, key=lambda x: x['distance'])
                    chosen_frame = best['frame']
                    chosen_side_frame = best['side_frame']
                    chosen_distance = best['distance']

                    # === هنا باقي التحليل ===
                    r_a_a, r_a_d = draw_ankel_arrow(chosen_frame, right_ankle, finger_xy_r, hip=right_hip, knee=right_knee, color=(255,0,255))
                    l_a_a, l_a_d = draw_ankel_arrow(chosen_frame, left_ankle, finger_xy_l, hip=left_hip, knee=left_knee, color=(255,0,0))

                    pelvis_angle = calculate_horizontal_pelvis_angle(left_hip, right_hip)
                    torso_angle = calculate_vertical_torso_angle(left_hip, right_hip, left_shoulder, right_shoulder)

                    if right_hip and right_knee and right_ankle:
                        draw_knee_angle(chosen_frame, right_hip, right_knee, right_ankle, color=(0,255,255))
                    if left_hip and left_knee and left_ankle:
                        draw_knee_angle(chosen_frame, left_hip, left_knee, left_ankle, color=(255,0,255))

                    # جانب جانبي
                    if side_right_hip and side_right_knee and side_right_ankle:
                        side_right_angle = draw_knee_angle(chosen_side_frame, side_right_hip, side_right_knee, side_right_ankle, color=(0,255,255))
                    if side_left_hip and side_left_knee and side_left_ankle:
                        side_left_angle = draw_knee_angle(chosen_side_frame, side_left_hip, side_left_knee, side_left_ankle, color=(255,0,255))

                    if side_left_hip and side_right_hip:
                        side_pelvis_angle = calculate_horizontal_pelvis_angle(side_left_hip, side_right_hip)
                    if side_left_hip and side_right_hip and side_left_shoulder and side_right_shoulder:
                        side_torso_angle_ = calculate_vertical_torso_angle(side_left_hip, side_right_hip, side_left_shoulder, side_right_shoulder)

                    processed_frame, direction, pitch, yaw, roll, bbox = detect_head_pose(frame_for_headpose) 

                    if box is not None and right_heel is not None:
                        y_perc, x_perc = calculate_ankle_ground_dis(right_heel, left_heel, foot, box)
                        x_perc = abs(100 - x_perc)
                        print(f"Ankle Y position: {y_perc:.1f} % | X position: {x_perc:.1f} %")
                        cv2.putText(chosen_frame, f"Ankle Y: {y_perc:.1f}% | X: {x_perc:.1f}%", (50,200), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)

                    # تصدير وتحليل
                    analysis_dict = export_analysis_to_json(
                        foot, direction, pelvis_angle, torso_angle,
                        {}, None, None, side_torso_angle_,
                        y_perc, x_perc, (r_a_a, r_a_d), (l_a_a, l_a_d),
                        real_distance
                    )

                    results.append({
                        "analysis": analysis_dict,
                        "front_frame": chosen_frame,
                        "side_frame": chosen_side_frame
                    })

                    # Reset
                    frame_history.clear()
                    increase_count = 0
                    last_distance = None
                    skip_frames = 50

    cap.release()
    cap2.release()
    
    if not results:
        raise ValueError("No receiving actions detected in the videos.")
    
    return results

