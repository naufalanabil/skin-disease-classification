import streamlit as st
import tensorflow as tf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import h5py

from PIL import Image

from database import save_prediction, get_history

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="Skin Disease Classification",
    page_icon="🩺",
    layout="wide"
)

# =====================================================
# CUSTOM CSS
# =====================================================

st.markdown("""
<style>

.main {
    padding-top: 20px;
}

.stButton button {
    width: 100%;
    border-radius: 10px;
    height: 45px;
    font-size: 16px;
}

</style>
""", unsafe_allow_html=True)

# =====================================================
# REBUILD MODEL ARCHITECTURE & LOAD WEIGHTS
# =====================================================

@st.cache_resource
def load_cached_model():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(base_dir, "saved_model", "skin_disease_model.keras")
    
    if not os.path.exists(model_path):
        st.error(f"❌ Model file missing! Looked inside: {model_path}")
        st.stop()
        
    try:
        # 1. Bangun struktur network manual sesuai logs metadata file
        inputs = tf.keras.layers.Input(shape=(224, 224, 3))
        
        base_model = tf.keras.applications.MobileNetV2(
            input_shape=(224, 224, 3),
            include_top=False,
            weights=None
        )
        x = base_model(inputs, training=False)
        
        x = tf.keras.layers.GlobalAveragePooling2D()(x)
        x = tf.keras.layers.Dropout(0.5)(x)
        dense_1 = tf.keras.layers.Dense(128, activation='relu', name='dense_2')(x)
        x = tf.keras.layers.Dropout(0.3)(x)
        dense_2 = tf.keras.layers.Dense(22, activation='softmax', name='dense_3')(x)
        
        rebuilt_model = tf.keras.Model(inputs, dense_2)
        
        # 2. Paksa baca isi file pake h5py supaya bypass error serialization config
        with h5py.File(model_path, 'r') as f:
            if 'model_weights' in f:
                w_group = f['model_weights']
                
                if 'dense_2' in w_group:
                    kernel = w_group['dense_2']['dense_2']['kernel:0'][:]
                    bias = w_group['dense_2']['dense_2']['bias:0'][:]
                    rebuilt_model.get_layer('dense_2').set_weights([kernel, bias])
                    
                if 'dense_3' in w_group:
                    kernel = w_group['dense_3']['dense_3']['kernel:0'][:]
                    bias = w_group['dense_3']['dense_3']['bias:0'][:]
                    rebuilt_model.get_layer('dense_3').set_weights([kernel, bias])
                    
        return rebuilt_model

    except Exception as e:
        st.warning(f"Map bypass fell back, attempting direct file stream mapping...")
        try:
            seq_model = tf.keras.Sequential([
                tf.keras.layers.Input(shape=(224, 224, 3)),
                tf.keras.applications.MobileNetV2(input_shape=(224, 224, 3), include_top=False, weights=None),
                tf.keras.layers.GlobalAveragePooling2D(),
                tf.keras.layers.Dropout(0.5),
                tf.keras.layers.Dense(128, activation='relu'),
                tf.keras.layers.Dropout(0.3),
                tf.keras.layers.Dense(22, activation='softmax')
            ])
            seq_model.load_weights(model_path, skip_mismatch=True)
            return seq_model
        except Exception as final_err:
            st.error(f"Failed to load weights: {final_err}")
            st.stop()

model = load_cached_model()

# =====================================================
# CLASS NAMES
# =====================================================

class_names = [
    "Acne", "Chickenpox", "Eczema", "Melanoma", "Psoriasis", "Ringworm",
    "Class_7", "Class_8", "Class_9", "Class_10", "Class_11", "Class_12",
    "Class_13", "Class_14", "Class_15", "Class_16", "Class_17", "Class_18",
    "Class_19", "Class_20", "Class_21", "Class_22"
]

# =====================================================
# SIDEBAR
# =====================================================

st.sidebar.title("🩺 Menu")

menu = st.sidebar.radio(
    "Navigation",
    [
        "Prediction",
        "History",
        "Dashboard"
    ]
)

# =====================================================
# PREDICTION PAGE
# =====================================================

if menu == "Prediction":

    st.title("🩺 Skin Disease Classification")

    st.write(
        "Upload a skin disease image for prediction"
    )

    uploaded_file = st.file_uploader(
        "Upload Image",
        type=["jpg", "jpeg", "png"]
    )

    if uploaded_file is not None:

        col1, col2 = st.columns(2)

        # =====================================================
        # SHOW IMAGE
        # =====================================================

        with col1:

            image = Image.open(uploaded_file)

            # Perbaikan: Mengganti use_column_width dengan use_container_width
            st.image(
                image,
                caption="Uploaded Image",
                use_container_width=True
            )

        # =====================================================
        # PREPROCESS
        # =====================================================

        image = image.convert("RGB")

        img = image.resize((224, 224))

        img_array = np.array(img)

        img_array = img_array / 255.0

        img_array = np.expand_dims(
            img_array,
            axis=0
        )

        # =====================================================
        # PREDICT BUTTON
        # =====================================================

        if st.button("Predict Disease"):

            with st.spinner("Processing prediction..."):

                prediction = model.predict(
                    img_array
                )

                predicted_class = np.argmax(
                    prediction
                )

                confidence = np.max(
                    prediction
                ) * 100

                disease_name = class_names[
                    predicted_class
                ]

            # =====================================================
            # RESULT
            # =====================================================

            with col2:

                st.success(
                    f"Prediction: {disease_name}"
                )

                st.info(
                    f"Confidence Score: {confidence:.2f}%"
                )

                # =====================================================
                # SAVE DATABASE
                # =====================================================

                try:

                    save_prediction(
                        uploaded_file.name,
                        disease_name,
                        float(confidence)
                    )

                    st.success(
                        "Prediction saved to database"
                    )

                except Exception as e:

                    st.error(
                        f"Database Error: {e}"
                    )

            # =====================================================
            # CONFIDENCE CHART
            # =====================================================

            st.subheader(
                "Prediction Confidence"
            )

            chart_data = pd.DataFrame({
                "Disease": class_names,
                "Confidence": prediction[0] * 100
            })

            st.bar_chart(
                chart_data.set_index(
                    "Disease"
                )
            )

            # =====================================================
            # TOP 3 PREDICTIONS
            # =====================================================

            st.subheader(
                "Top Predictions"
            )

            top_indices = np.argsort(
                prediction[0]
            )[-3:][::-1]

            for idx in top_indices:

                st.write(
                    f"{class_names[idx]} : "
                    f"{prediction[0][idx] * 100:.2f}%"
                )

# =====================================================
# HISTORY PAGE
# =====================================================

elif menu == "History":

    st.title("📜 Prediction History")

    try:

        history = get_history()

        if history:

            df = pd.DataFrame(history)

            st.dataframe(
                df,
                use_container_width=True
            )

        else:

            st.warning(
                "No prediction history available"
            )

    except Exception as e:

        st.error(
            f"Database Error: {e}"
        )

# =====================================================
# DASHBOARD PAGE
# =====================================================

elif menu == "Dashboard":

    st.title("📊 Dashboard Statistics")

    try:

        history = get_history()

        if history:

            df = pd.DataFrame(history)

            # =====================================================
            # TOTAL PREDICTIONS
            # =====================================================

            total_prediction = len(df)

            st.metric(
                "Total Predictions",
                total_prediction
            )

            # =====================================================
            # PREDICTION COUNT
            # =====================================================

            st.subheader(
                "Disease Prediction Count"
            )

            prediction_count = (
                df["prediction"]
                .value_counts()
            )

            st.bar_chart(
                prediction_count
            )

            # =====================================================
            # AVERAGE CONFIDENCE
            # =====================================================

            st.subheader(
                "Average Confidence"
            )

            avg_confidence = (
                df.groupby("prediction")
                ["confidence"]
                .mean()
            )

            st.line_chart(
                avg_confidence
            )

            # =====================================================
            # RECENT PREDICTIONS
            # =====================================================

            st.subheader(
                "Recent Predictions"
            )

            st.dataframe(
                df.tail(10),
                use_container_width=True
            )

        else:

            st.warning(
                "No dashboard data available"
            )

    except Exception as e:

        st.error(
            f"Dashboard Error: {e}"
        )