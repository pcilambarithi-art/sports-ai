"""Generate a polished, multi-page PDF Project Report for ApexPulse AI-Powered Sports Coaching System."""

from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

OUTPUT_PDF = Path(r"D:\sports-coaching-system\ApexPulse_AI_Sports_Coaching_Project_Report.pdf")

PURPLE_DARK = colors.HexColor("#1A0B2E")
PURPLE_PRIMARY = colors.HexColor("#7E22CE")
FUCHSIA_ACCENT = colors.HexColor("#C026D3")
CYAN_ACCENT = colors.HexColor("#0891B2")
SLATE_TEXT = colors.HexColor("#1E293B")
MUTED_TEXT = colors.HexColor("#475569")
LIGHT_BG = colors.HexColor("#F5F0FF")
ROW_ALT = colors.HexColor("#FAF7FF")
BORDER_COLOR = colors.HexColor("#D8B4FE")


def _header_footer(canvas, doc):
    canvas.saveState()
    w, h = A4
    # Top accent bar
    canvas.setFillColor(PURPLE_DARK)
    canvas.rect(0, h - 14 * mm, w, 14 * mm, fill=1, stroke=0)
    canvas.setFillColor(FUCHSIA_ACCENT)
    canvas.rect(0, h - 15 * mm, w * 0.55, 1.2 * mm, fill=1, stroke=0)
    canvas.setFillColor(CYAN_ACCENT)
    canvas.rect(w * 0.55, h - 15 * mm, w * 0.45, 1.2 * mm, fill=1, stroke=0)

    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(18 * mm, h - 9.5 * mm, "APEXPULSE AI  |  AI-POWERED SPORTS COACHING SYSTEM")
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(w - 18 * mm, h - 9.5 * mm, "Technical Implementation & Requirements Report")

    # Footer
    canvas.setStrokeColor(BORDER_COLOR)
    canvas.setLineWidth(0.6)
    canvas.line(18 * mm, 14 * mm, w - 18 * mm, 14 * mm)
    canvas.setFillColor(MUTED_TEXT)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(18 * mm, 9 * mm, "GitHub: https://github.com/pcilambarithi-art/sports-ai")
    canvas.drawRightString(w - 18 * mm, 9 * mm, f"Page {doc.page}")
    canvas.restoreState()


def build_pdf():
    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=22 * mm,
        bottomMargin=20 * mm,
        title="ApexPulse AI-Powered Sports Coaching System - Project Report",
        author="ApexPulse AI Engineering",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "HeroTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=27,
        textColor=PURPLE_DARK,
        alignment=0,
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "HeroSub",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=15,
        textColor=MUTED_TEXT,
        spaceAfter=12,
    )
    h1_style = ParagraphStyle(
        "SectionH1",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=13.5,
        leading=18,
        textColor=PURPLE_PRIMARY,
        spaceBefore=12,
        spaceAfter=6,
    )
    h2_style = ParagraphStyle(
        "TaskH2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=PURPLE_DARK,
        spaceBefore=10,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.2,
        leading=13.5,
        textColor=SLATE_TEXT,
        spaceAfter=4,
    )
    cell_style = ParagraphStyle(
        "Cell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.3,
        leading=11.5,
        textColor=SLATE_TEXT,
    )
    cell_bold = ParagraphStyle(
        "CellBold",
        parent=cell_style,
        fontName="Helvetica-Bold",
        textColor=PURPLE_DARK,
    )

    story = []

    # Cover / Executive Header
    story.append(Paragraph("ApexPulse AI-Powered Sports Coaching System", title_style))
    story.append(
        Paragraph(
            "Complete Requirements Traceability, Architecture, AI/ML Model Integration, Technology Stack, "
            "and Rationale Report — Mapping Every Requirement from the Project Specification PDF.",
            subtitle_style,
        )
    )
    story.append(HRFlowable(width="100%", thickness=1.5, color=PURPLE_PRIMARY, spaceAfter=10))

    # Executive Summary Table
    summary_data = [
        [Paragraph("<b>Project Repository</b>", cell_bold), Paragraph("https://github.com/pcilambarithi-art/sports-ai (Branch: main)", cell_style)],
        [Paragraph("<b>Primary Trained Model</b>", cell_bold), Paragraph("Existing D:\\V3 ExtraTreesRegressor (300 trees, 2.93 GB, preserved 100% read-only) — Verified Test R²: 91.81%, MAE: 61.36 kcal, 5-Fold CV R²: 91.71%", cell_style)],
        [Paragraph("<b>Companion Trained AI</b>", cell_bold), Paragraph("HistGradientBoosting Strain & Readiness Classifier (97.00% Test Accuracy, 97.14% Macro-F1 on 70,000+ rows) + TF-IDF Bi-Gram & LinearSVC Semantic Virtual Coach (30 curated knowledge docs, 2,081 bi-gram vocab)", cell_style)],
        [Paragraph("<b>Application Scale</b>", cell_bold), Paragraph("49 REST & WebSocket API Endpoints • 22 Relational Database Tables (Alembic-migrated) • 12 Glossy Purple-Black Neon React Modules • OpenCV Computer Vision Video Pipeline", cell_style)],
        [Paragraph("<b>Verification Status</b>", cell_bold), Paragraph("Pytest Full Integration Suite PASSED • Live 2.93 GB Model HTTP Inference Test PASSED • Frontend Production Build PASSED (0 TS errors, 0 warnings) • Live Public HTTPS Verified (HTTP 200)", cell_style)],
    ]
    summary_tbl = Table(summary_data, colWidths=[45 * mm, 129 * mm])
    summary_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), LIGHT_BG),
                ("BACKGROUND", (1, 0), (1, -1), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.6, BORDER_COLOR),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    story.append(summary_tbl)
    story.append(Spacer(1, 8))

    # Detailed Task-by-Task Breakdown
    story.append(Paragraph("Detailed PDF Task Breakdown: What We Built, What We Used & Why", h1_style))

    tasks = [
        (
            "1. User Management & Role-Based Access Control (RBAC)",
            "Implemented secure user registration, login, persistent JWT sessions, individual Athlete and Coach profile management, Coach-to-Athlete roster assignments, and Admin role/status controls across all four required roles (Admin, Coach/Trainer, Sports Analyst, Athlete/Player).",
            "FastAPI, bcrypt (12-round salted password hashing), python-jose (JWT HS256), SQLAlchemy 2.0 ORM tables (users, athlete_profiles, coach_profiles, coach_athlete_links), backend/app/core/security.py, and AthletesProfilesPage.tsx.",
            "Protects sensitive athlete biometric and training data using industry-standard salted password hashing and stateless JWT authorization, strictly enforcing role boundaries so athletes view only their authorized data while coaches, analysts, and admins manage team operations safely.",
        ),
        (
            "2. AI-Driven Performance Analysis (Existing Model + Companion AI)",
            "Integrated your existing trained D:\\V3 calorie burn model read-only for single-workout and batch CSV/Excel inference, returning actual predicted calories, burn rate (kcal/min), real 300-tree ensemble uncertainty bands (10th–90th percentile & std), 70,000-row dataset percentile rankings, global feature importances, and live counterfactual 'what-if' sensitivity deltas — alongside a newly trained Companion Strain & Readiness Classifier.",
            "Existing scikit-learn ExtraTreesRegressor (300 trees, Test R² 91.81%, MAE 61.36 kcal) + trained_models/preprocessor.pkl wrapped in thread-safe singleton backend/app/ml/model_service.py; HistGradientBoostingClassifier (97.00% Test Accuracy, 97.14% Macro-F1) in backend/app/ml/coaching_ai_engine.py; Recharts dashboards in AiPredictionLabPage.tsx.",
            "Strictly preserves your existing trained model without fabricating or replacing it. Loading the 2.93 GB pickle once in a non-blocking background thread lets the API boot instantly with low memory overhead, while 300-tree uncertainty bands and live what-if re-runs turn predictions into transparent, actionable coaching intelligence.",
        ),
        (
            "3. Personalized Training Programs & Adaptive Learning Paths",
            "Built an AI-powered weekly & daily training generator tailored to each athlete's sport, goal (Weight Loss, Endurance, Muscle Gain, Flexibility, General Fitness), experience level, and logged workout history. Populates real expected session calories via the trained model, tracks completion with RPE feedback, and dynamically adapts remaining sessions when 'Adapt Plan from Feedback' is clicked.",
            "analytics_service.py (generate_training_program & adapt_training_program), training.py router, relational tables training_programs & training_sessions, and TrainingProgramsPage.tsx.",
            "Static workout templates ignore fatigue and adaptation speed. Automatically adjusting volume and target heart rate from actual logged RPE feedback—and recalculating expected energy expenditure with your trained model—delivers genuinely adaptive coaching schedules.",
        ),
        (
            "4. Injury Prediction, Anomaly Detection & Prevention",
            "Developed a workload risk & anomaly monitoring module calculating 7-day Acute Load vs. 28-day Chronic Load, Acute:Chronic Workload Ratio (ACWR), statistical z-score session-duration anomalies, sustained high heart rate exposure, and sleep/hydration recovery deficits. Generates a 0–100 risk score, preventive exercises, load modifications, and coach intervention alerts with acknowledgement workflow.",
            "NumPy statistical workload & z-score calculations in assess_injury_risk, injury.py router, injury_risk_assessments table, and InjuryPreventionPage.tsx.",
            "Because the existing D:\\V3 model predicts calorie expenditure (not clinical injury diagnoses), transparent sports-science ACWR heuristics and statistical anomaly detection provide honest overuse risk monitoring with a clear non-medical disclaimer.",
        ),
        (
            "5. Game Strategy Optimization & Scenario Simulation",
            "Built opponent scouting profile management (explicitly highlighting unavailable stats rather than fabricating values), head-to-head comparison against actual logged athlete/team speed and endurance, data-backed counter-strategy generation, and an interactive tactical scenario simulator with tempo-shift and defensive-balance sliders.",
            "generate_game_strategy service, strategy.py router, opponents & game_strategies database tables, and GameStrategyPage.tsx.",
            "Gives coaches and analysts structured tactical planning grounded strictly in verified opponent scouting records and real team performance logs without misleading invented opponent statistics.",
        ),
        (
            "6. Real-Time Performance Tracking (Wearables & IoT)",
            "Built a live WebSocket telemetry dashboard tracking Heart Rate, Speed, Distance, Duration, Calories, Muscle Load, and Fatigue, paired with a manual live check-in logger and an API-key-secured wearable/IoT webhook (POST /api/telemetry/webhook). Explicitly displays 'Awaiting Wearable / IoT Sensor Integration' when no external hardware stream is active.",
            "FastAPI WebSockets with strict JWT RBAC (ws_manager.py & telemetry.py), telemetry_readings table, and live Recharts streaming in TelemetryPage.tsx.",
            "WebSockets deliver sub-second telemetry updates without wasteful polling, while the authenticated webhook API lets Garmin, Polar, Apple Health bridges, or ESP32/BLE IoT sensors stream directly into the platform without ever simulating fake live vitals.",
        ),
        (
            "7. Virtual Coaching Assistant (Chatbot + Voice Assistant)",
            "Built a conversational and voice-enabled AI coach that answers sports-science, training, nutrition, recovery, biomechanics, and tactical questions, summarizes authorized athlete DB reports/schedules/injury risks, runs live calorie predictions inside chat, and lets coaches teach new team playbooks stored in the database.",
            "Trained TF-IDF Bi-Gram Semantic Retriever (2,081 features) + LinearSVC Intent Classifier trained on the coaching_knowledge DB table (30 curated entries + custom additions), browser Web Speech API (SpeechRecognition mic + SpeechSynthesis TTS), and VirtualCoachPage.tsx.",
            "Runs 100% locally at zero external LLM cost, anchors responses in real authenticated database records and live trained ML outputs, supports hands-free voice guidance during training, and continuously expands as coaches add knowledge.",
        ),
        (
            "8. Video Analysis & Visual Feedback (Computer Vision)",
            "Created a validated sports video upload pipeline (.mp4, .avi, .mov, .mkv, .webm, up to 150 MB) that extracts metadata, computes frame-to-frame motion intensity curves, tracks primary subject bounding boxes and centroid spatial trajectories, identifies peak-activity key moments, renders annotated PNG keyframes with HUD overlays, and optionally links athlete biometrics to the trained calorie model.",
            "OpenCV (opencv-python-headless) using Farneback Dense Optical Flow (cv2.calcOpticalFlowFarneback) and MOG2 Background Subtraction / Contour Tracking in backend/app/cv/video_analyzer.py, video.py router, video_analyses table, and VideoAnalysisPage.tsx.",
            "OpenCV processes real sports footage reliably on standard CPUs without expensive GPU requirements, provides objective movement tempo and spatial coverage metrics, and stays transparently separated from the tabular calorie model.",
        ),
        (
            "9. Skill Assessment, Scoring & Predictive Analytics",
            "Built a transparent 5-pillar weighted skill scoring system (Consistency 25%, Energy Output 25%, Aerobic Efficiency 20%, Workload Capacity 15%, Recovery Discipline 15%), peer cohort ranking against real database athletes + 70,000-row dataset percentiles, linear performance trend forecasting, and peak competition window tapering estimates.",
            "evaluate_skill_assessment & compute_predictive_analytics (NumPy linear regression polyfit), skills_gamification.py router, skill_assessments table, and Radar/Line Recharts in SkillAssessmentPage.tsx.",
            "Documented, auditable scoring criteria eliminate arbitrary or invented 'professional benchmarks' and clearly show athletes which measurable pillars improved over time.",
        ),
        (
            "10. Gamification & Motivation",
            "Implemented automatic milestone achievement badges (8 badges evaluated from real DB activity), XP-based team leaderboards and rankings, 14-day training consistency streaks, and coach-published training challenges with join and progress logging.",
            "evaluate_user_achievements & build_leaderboard services, relational tables (achievements, user_achievements, challenges, challenge_participations), and GamificationPage.tsx.",
            "Rewarding real logged sessions, predictions, video analyses, and completed challenges boosts long-term athlete adherence while keeping rankings strictly tied to genuine database activity.",
        ),
        (
            "11. Non-Functional Requirements: Database, UI/UX, Security, Testing & Cloud/Zero-AWS Deployment",
            "Built a 22-table relational schema with Alembic migrations (SQLite local default + PostgreSQL 16 + MySQL 8 drivers), glossy Obsidian Black + Royal Purple multi-color neon-glow UI with Dark/Light themes and route-based code splitting, CSV exports for third-party analytics, structured request-timing headers, comprehensive pytest suites, GitHub repository, live free HTTPS via Cloudflare Tunnel, plus Docker Compose, Netlify, Railway, and AWS Terraform IaC.",
            "React 19, TypeScript, Vite 8, Tailwind CSS v4, Recharts, Lucide Icons, FastAPI, SQLAlchemy 2.0, Alembic, psycopg, pymysql, Pytest, Cloudflare Tunnel (cloudflared), Docker Compose, Terraform (VPC/RDS/S3/EC2/CloudWatch), GitHub.",
            "Provides production-grade maintainability, zero-warning fast frontend builds (1.45s), cross-database portability, verifiable automated testing, and flexible deployment—running free today without AWS while remaining ready for Railway, Netlify, VPS, or AWS scale-out.",
        ),
    ]

    for title, what_did, what_used, why_used in tasks:
        story.append(Paragraph(title, h2_style))
        block_tbl = Table(
            [
                [Paragraph("<b>What We Built</b>", cell_bold), Paragraph(what_did, cell_style)],
                [Paragraph("<b>What We Used</b>", cell_bold), Paragraph(what_used, cell_style)],
                [Paragraph("<b>Why We Used It</b>", cell_bold), Paragraph(why_used, cell_style)],
            ],
            colWidths=[32 * mm, 142 * mm],
        )
        block_tbl.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), LIGHT_BG),
                    ("BACKGROUND", (1, 0), (1, 0), colors.white),
                    ("BACKGROUND", (1, 1), (1, 1), ROW_ALT),
                    ("BACKGROUND", (1, 2), (1, 2), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4.5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(block_tbl)
        story.append(Spacer(1, 5))

    story.append(PageBreak())

    # Verified AI / ML Metrics & Database Summary Page
    story.append(Paragraph("Verified AI / ML Model & Testing Metrics Summary", h1_style))
    metrics_tbl = Table(
        [
            [
                Paragraph("<b>Component</b>", cell_bold),
                Paragraph("<b>Algorithm / Engine</b>", cell_bold),
                Paragraph("<b>Training Data</b>", cell_bold),
                Paragraph("<b>Verified Result</b>", cell_bold),
            ],
            [
                Paragraph("Primary Calorie Predictor (Preserved)", cell_style),
                Paragraph("ExtraTreesRegressor (300 trees, scikit-learn 1.9.1)", cell_style),
                Paragraph("D:\\V3 70,000 workout rows (25 encoded features)", cell_style),
                Paragraph("Test R²: 91.81% | MAE: 61.36 kcal | CV R²: 91.71%", cell_style),
            ],
            [
                Paragraph("Companion Strain & Readiness AI", cell_style),
                Paragraph("HistGradientBoostingClassifier (Continuous Learning)", cell_style),
                Paragraph("70,000 dataset rows + live DB performance_records", cell_style),
                Paragraph("Test Accuracy: 97.00% | Macro-F1: 97.14%", cell_style),
            ],
            [
                Paragraph("Virtual Coach Semantic NLP", cell_style),
                Paragraph("TF-IDF Bi-Gram Retriever + LinearSVC Intent Classifier", cell_style),
                Paragraph("30 curated DB knowledge docs + custom coach entries", cell_style),
                Paragraph("2,081 bi-gram features • Real-time DB + ML fusion", cell_style),
            ],
            [
                Paragraph("Video Movement Breakdown", cell_style),
                Paragraph("OpenCV Farneback Optical Flow + MOG2 Contours", cell_style),
                Paragraph("Uploaded sports clips (.mp4/.avi/.mov/.mkv/.webm)", cell_style),
                Paragraph("Motion timeline, centroid map & annotated PNGs", cell_style),
            ],
            [
                Paragraph("Automated Test Suites", cell_style),
                Paragraph("Pytest + FastAPI TestClient + Vite TypeScript", cell_style),
                Paragraph("Full API, RBAC, OpenCV, Companion AI & Live 2.93 GB ML", cell_style),
                Paragraph("test_api.py PASSED • test_real_model_inference.py PASSED • vite build 0 errors", cell_style),
            ],
        ],
        colWidths=[38 * mm, 46 * mm, 44 * mm, 46 * mm],
    )
    metrics_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), LIGHT_BG),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ROW_ALT]),
                ("GRID", (0, 0), (-1, -1), 0.55, BORDER_COLOR),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(metrics_tbl)
    story.append(Spacer(1, 10))

    # 22-Table Database Schema Overview
    story.append(Paragraph("Relational Database Architecture (22 Alembic-Migrated Tables)", h1_style))
    story.append(
        Paragraph(
            "Designed with SQLAlchemy 2.0 and Alembic migrations for full portability across SQLite (local zero-config), "
            "MySQL 8 (pymysql), and PostgreSQL 16 (psycopg / Docker / RDS):",
            body_style,
        )
    )
    db_tbl = Table(
        [
            [Paragraph("<b>Domain Group</b>", cell_bold), Paragraph("<b>Database Tables</b>", cell_bold)],
            [Paragraph("Users & Access Control", cell_style), Paragraph("users, athlete_profiles, coach_profiles, coach_athlete_links, activity_logs", cell_style)],
            [Paragraph("AI Models & Knowledge", cell_style), Paragraph("ai_predictions, coaching_knowledge, ai_model_training_runs, chat_messages", cell_style)],
            [Paragraph("Performance & Telemetry", cell_style), Paragraph("performance_records, telemetry_readings, video_analyses, skill_assessments", cell_style)],
            [Paragraph("Coaching & Risk Prevention", cell_style), Paragraph("training_programs, training_sessions, injury_risk_assessments", cell_style)],
            [Paragraph("Strategy & Gamification", cell_style), Paragraph("opponents, game_strategies, achievements, user_achievements, challenges, challenge_participations", cell_style)],
        ],
        colWidths=[48 * mm, 126 * mm],
    )
    db_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), LIGHT_BG),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ROW_ALT]),
                ("GRID", (0, 0), (-1, -1), 0.55, BORDER_COLOR),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(db_tbl)
    story.append(Spacer(1, 10))

    # Deployment Options Summary
    story.append(Paragraph("Deployment & Access Options (Zero-AWS and Cloud Ready)", h1_style))
    story.append(
        Paragraph(
            "• <b>Zero-AWS Local + Free Public HTTPS:</b> Run start-local.ps1 + start-public-tunnel.ps1 (Cloudflare Tunnel) "
            "to serve the complete system including the 2.93 GB trained model over HTTPS for free.<br/>"
            "• <b>Non-AWS Cloud / Self-Hosted:</b> docker-compose.yml (PostgreSQL 16 + FastAPI + Nginx), railway.toml (Railway Docker), "
            "and netlify.toml (Netlify React Frontend).<br/>"
            "• <b>Optional AWS Production IaC:</b> deploy/aws/main.tf (VPC, encrypted RDS PostgreSQL 16, S3 model storage, EC2 m6i.xlarge, CloudWatch).",
            body_style,
        )
    )

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    print(f"PDF generated successfully: {OUTPUT_PDF} ({OUTPUT_PDF.stat().st_size:,} bytes)")


if __name__ == "__main__":
    build_pdf()
