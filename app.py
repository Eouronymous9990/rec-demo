import streamlit as st
import cv2
from PIL import Image
import os
import csv
import io
from analyzer import analyze_videos

st.set_page_config(page_title="Tactiq", layout="wide", initial_sidebar_state="collapsed", page_icon="icon.png")

if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'csv_data' not in st.session_state:
    st.session_state.csv_data = None

st.title("Football Analysis")
st.markdown("Analyze football techniques with biomechanical insights from front and side view videos")

col1, col2 = st.columns(2)
with col1:
    front_video = st.file_uploader("Upload Front View Video (Optional)", type=["mp4"])
with col2:
    side_video = st.file_uploader("Upload Side View Video (Mandatory)", type=["mp4"])

if st.button("Analyze", key="analyze_button"):
    st.session_state.analysis_results = None
    st.session_state.csv_data = None
    
    if side_video:
        with st.spinner("Processing videos... This may take a few minutes."):
            front_path = None
            side_path = "temp_side.mp4"
            
            if front_video:
                front_path = "temp_front.mp4"
                with open(front_path, "wb") as f:
                    f.write(front_video.read())
            
            with open(side_path, "wb") as f:
                f.write(side_video.read())
            
            try:
                results = analyze_videos(front_path=front_path, side_path=side_path)
                st.session_state.analysis_results = results
                
                csv_buffer = io.StringIO()
                csv_writer = csv.writer(csv_buffer)
                
                header = [
                    "Detection_ID", "Receiving_Foot", "Head_Orientation",
                    "Heel_Ball_Distance_Y_%", "Heel_Ball_Distance_X_%",
                    "Ankle_Ball_Distance_cm",
                    "Front_Pelvis_Angle_deg", "Front_Torso_Angle_deg",
                    "Ankle_Y_Position_%", "Ankle_X_Position_%",
                    "Right_Ankle_Angle_deg", "Right_Ankle_Distance_px",
                    "Left_Ankle_Angle_deg", "Left_Ankle_Distance_px",
                    "Side_Supporting_Knee_Angle_deg", "Side_Torso_Angle_deg",
                    "Timestamp"
                ]
                csv_writer.writerow(header)
                
                for idx, result in enumerate(results, 1):
                    analysis = result["analysis"]
                    
                    x_perc_adjusted = None
                    if analysis.get("normalized_receiving_ankle_position") and analysis["normalized_receiving_ankle_position"].get("X_position_percentage") is not None:
                        x_pct = analysis['normalized_receiving_ankle_position']['X_position_percentage']
                        x_perc_adjusted = abs(100 - x_pct)
                    
                    row = [
                        idx,
                        analysis.get("receiving_foot", "N/A"),
                        analysis.get("head_direction", "N/A"),
                        f"{analysis.get('heel_ball_percentage_y', 'N/A'):.1f}" if analysis.get('heel_ball_percentage_y') is not None else "N/A",
                        f"{analysis.get('heel_ball_percentage_x', 'N/A'):.1f}" if analysis.get('heel_ball_percentage_x') is not None else "N/A",
                        f"{analysis.get('ankle_ball_dist_cm', 'N/A'):.1f}" if analysis.get('ankle_ball_dist_cm') is not None else "N/A",
                        analysis.get("front_pelvis_angle", "N/A"),
                        analysis.get("front_torso_angle", "N/A"),
                        analysis["normalized_receiving_ankle_position"]["Y_position_percentage"] if analysis.get("normalized_receiving_ankle_position") and analysis["normalized_receiving_ankle_position"].get("Y_position_percentage") is not None else "N/A",
                        f"{x_perc_adjusted:.1f}" if x_perc_adjusted is not None else "N/A",
                        analysis.get("right_ankle_angle", "N/A"),
                        analysis.get("right_ankle_distance", "N/A"),
                        analysis.get("left_ankle_angle", "N/A"),
                        analysis.get("left_ankle_distance", "N/A"),
                        analysis.get("side_supporting_knee_angle", "N/A"),
                        analysis.get("side_torso_angle", "N/A"),
                        analysis.get("timestamp", "N/A")
                    ]
                    csv_writer.writerow(row)
                
                st.session_state.csv_data = csv_buffer.getvalue()
                
            except Exception as e:
                st.error(f"Error during analysis: {str(e)}")
            finally:
                if front_path and os.path.exists(front_path):
                    os.remove(front_path)
                if os.path.exists(side_path):
                    os.remove(side_path)
    else:
        st.warning("Please upload the side view video to proceed (front view is optional).")

if st.session_state.analysis_results:
    results = st.session_state.analysis_results
    
    st.success(f"Analysis complete! {len(results)} detection(s) found.")
    
    if st.session_state.csv_data:
        st.download_button(
            label="Download CSV Report",
            data=st.session_state.csv_data,
            file_name="football_analysis_report.csv",
            mime="text/csv",
            key="download_csv"
        )
    
    for idx, result in enumerate(results, 1):
        st.markdown("<hr>", unsafe_allow_html=True)
        st.header(f"Detection {idx}")
        analysis = result["analysis"]
        
        st.subheader("Basic Information")
        basic_info = [
            {"Metric": "Receiving Foot", "Value": analysis["receiving_foot"].capitalize() if analysis["receiving_foot"] else "Not Detected"},
            {"Metric": "Head Orientation", "Value": analysis["head_direction"] if analysis["head_direction"] else "Not Detected"}
        ]
        st.table(basic_info)
        
        if result["front_frame"] is not None:
            st.subheader("Front View Biomechanical Analysis")
            front_metrics = []
            
            if analysis.get("heel_ball_percentage_y") is not None:
                front_metrics.append({
                    "Metric": "Heel-Ball Distance Y",
                    "Value": f"{analysis['heel_ball_percentage_y']:.1f}%"
                })
            
            if analysis.get("heel_ball_percentage_x") is not None:
                front_metrics.append({
                    "Metric": "Heel-Ball Distance X",
                    "Value": f"{analysis['heel_ball_percentage_x']:.1f}%"
                })
            
            front_metrics.append({
                "Metric": "Ankle-Ball Distance (cm)",
                "Value": f"{analysis['ankle_ball_dist_cm']:.1f} cm" if analysis.get('ankle_ball_dist_cm') is not None else "N/A"
            })
            
            front_metrics.append({
                "Metric": "Pelvis Angle",
                "Value": f"{analysis['front_pelvis_angle']}°" if analysis["front_pelvis_angle"] is not None else "N/A"
            })
            
            front_metrics.append({
                "Metric": "Torso Angle",
                "Value": f"{analysis['front_torso_angle']}°" if analysis["front_torso_angle"] is not None else "N/A"
            })
            
            if analysis["normalized_receiving_ankle_position"] and analysis["normalized_receiving_ankle_position"].get("Y_position_percentage") is not None:
                front_metrics.append({
                    "Metric": "Ankle Y Position (% of Body)",
                    "Value": f"{analysis['normalized_receiving_ankle_position']['Y_position_percentage']}%"
                })
            else:
                front_metrics.append({
                    "Metric": "Ankle Y Position (% of Body)",
                    "Value": "N/A"
                })
            
            if analysis["normalized_receiving_ankle_position"] and analysis["normalized_receiving_ankle_position"].get("X_position_percentage") is not None:
                x_pct = analysis['normalized_receiving_ankle_position']['X_position_percentage']
                x_adjusted = abs(100 - x_pct)
                front_metrics.append({
                    "Metric": "Ankle X Position (% of Body)",
                    "Value": f"{x_adjusted:.1f}%"
                })
            else:
                front_metrics.append({
                    "Metric": "Ankle X Position (% of Body)",
                    "Value": "N/A"
                })
            
            st.table(front_metrics)
            
            st.markdown("**Ankle Values (for reference):**")
            ankle_ref = []
            if analysis.get("right_ankle_angle") is not None or analysis.get("right_ankle_distance") is not None:
                ankle_ref.append({
                    "Side": "Right Ankle",
                    "Angle": f"{analysis['right_ankle_angle']}°" if analysis.get("right_ankle_angle") else "N/A",
                    "Distance (px)": f"{analysis['right_ankle_distance']} px" if analysis.get("right_ankle_distance") else "N/A"
                })
            if analysis.get("left_ankle_angle") is not None or analysis.get("left_ankle_distance") is not None:
                ankle_ref.append({
                    "Side": "Left Ankle",
                    "Angle": f"{analysis['left_ankle_angle']}°" if analysis.get("left_ankle_angle") else "N/A",
                    "Distance (px)": f"{analysis['left_ankle_distance']} px" if analysis.get("left_ankle_distance") else "N/A"
                })
            if ankle_ref:
                st.table(ankle_ref)
        
        st.subheader("Side View Biomechanical Analysis")
        side_metrics = []
        
        side_metrics.append({
            "Metric": "Supporting Knee Angle",
            "Value": f"{analysis['side_supporting_knee_angle']}°" if analysis.get("side_supporting_knee_angle") is not None else "N/A"
        })
        
        side_metrics.append({
            "Metric": "Torso Angle",
            "Value": f"{analysis['side_torso_angle']}°" if analysis.get("side_torso_angle") is not None else "N/A"
        })
        
        st.table(side_metrics)
        
        st.markdown(f"**Analysis Timestamp:** {analysis['timestamp']}")
        
        if result["front_frame"] is not None:
            col_img1, col_img2 = st.columns(2)
        else:
            col_img1, col_img2 = st.columns([0.001, 1])
        
        if result["front_frame"] is not None:
            with col_img1:
                st.subheader("Front View Frame")
                front_img = Image.fromarray(cv2.cvtColor(result["front_frame"], cv2.COLOR_BGR2RGB))
                st.image(front_img, use_container_width=True)
                
                front_img_buffer = io.BytesIO()
                front_img.save(front_img_buffer, format='PNG')
                front_img_bytes = front_img_buffer.getvalue()
                
                st.download_button(
                    label="Download Front View Image",
                    data=front_img_bytes,
                    file_name=f"front_view_detection_{idx}.png",
                    mime="image/png",
                    key=f"download_front_{idx}"
                )
        
        with col_img2:
            st.subheader("Side View Frame")
            side_img = Image.fromarray(cv2.cvtColor(result["side_frame"], cv2.COLOR_BGR2RGB))
            st.image(side_img, use_container_width=True)
            
            side_img_buffer = io.BytesIO()
            side_img.save(side_img_buffer, format='PNG')
            side_img_bytes = side_img_buffer.getvalue()
            
            st.download_button(
                label="Download Side View Image",
                data=side_img_bytes,
                file_name=f"side_view_detection_{idx}.png",
                mime="image/png",
                key=f"download_side_{idx}"
            )
