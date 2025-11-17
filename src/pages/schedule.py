"""
Schedule Page - Display and manage personalized study schedules
"""

import streamlit as st
from datetime import datetime, timedelta, date
from typing import List, Optional

from src.core.scheduler import StudyScheduler, DailySchedule
from src.data.db import Database
from src.core.auth import SessionManager


def show_schedule_page():
    """Display the study schedule page with calendar view and daily plans"""
    st.title("📅 Study Schedule")
    
    # Ensure authenticated
    if not SessionManager.is_authenticated(st.session_state):
        st.error("Please log in to view your schedule")
        st.stop()
    
    # Initialize
    db = Database()
    user_id = SessionManager.get_user_id(st.session_state)
    
    if not user_id:
        st.error("Please log in to view your schedule")
        return
    
    scheduler = StudyScheduler(db, user_id)
    
    # Sidebar controls
    with st.sidebar:
        st.header("⚙️ Schedule Settings")
        
        # Date range selector
        view_mode = st.radio(
            "View",
            ["This Week", "Next Week", "Custom Range"],
            help="Select the time period to view"
        )
        
        if view_mode == "This Week":
            today = date.today()
            start_date = today - timedelta(days=today.weekday())  # Monday
            num_days = 7
        elif view_mode == "Next Week":
            today = date.today()
            start_date = today - timedelta(days=today.weekday()) + timedelta(days=7)
            num_days = 7
        else:  # Custom Range
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date", value=date.today())
            with col2:
                end_date = st.date_input("End Date", value=date.today() + timedelta(days=6))
            num_days = (end_date - start_date).days + 1
        
        # Subject filter
        st.subheader("Focus Subjects")
        focus_physics = st.checkbox("Physics", value=True)
        focus_chemistry = st.checkbox("Chemistry", value=True)
        focus_math = st.checkbox("Mathematics", value=True)
        
        focus_subjects = []
        if focus_physics:
            focus_subjects.append("Physics")
        if focus_chemistry:
            focus_subjects.append("Chemistry")
        if focus_math:
            focus_subjects.append("Mathematics")
        
        # Generate button
        st.divider()
        if st.button("🔄 Regenerate Schedule", use_container_width=True):
            with st.spinner("Generating personalized schedule..."):
                schedules = scheduler.generate_schedule(
                    start_date=start_date,
                    num_days=num_days,
                    focus_subjects=focus_subjects if focus_subjects else None
                )
                
                # Save all schedules
                for schedule in schedules:
                    scheduler.save_schedule(schedule)
                
                st.success(f"Generated {num_days}-day schedule!")
                st.rerun()
    
    # Main content area
    st.markdown("---")
    
    # Load schedules
    schedules = scheduler.generate_schedule(
        start_date=start_date,
        num_days=num_days,
        focus_subjects=focus_subjects if focus_subjects else None
    )
    
    # Show statistics
    show_schedule_stats(scheduler, start_date, start_date + timedelta(days=num_days-1))
    
    st.markdown("---")
    
    # Display daily schedules
    if not schedules:
        st.info("No schedule generated yet. Use the settings in the sidebar to create your schedule.")
        return
    
    # Tabs for each day
    tab_names = [schedule.date.strftime("%a, %b %d") for schedule in schedules]
    tabs = st.tabs(tab_names)
    
    for tab, schedule in zip(tabs, schedules):
        with tab:
            show_daily_schedule(scheduler, schedule, user_id)


def show_schedule_stats(scheduler: StudyScheduler, start_date: date, end_date: date):
    """Display statistics about the schedule"""
    stats = scheduler.get_schedule_stats(start_date, end_date)
    
    if stats['total_days'] == 0:
        return
    
    st.subheader("📊 Schedule Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Days Scheduled",
            stats['total_days'],
            help="Total number of days with schedules"
        )
    
    with col2:
        st.metric(
            "Days Completed",
            stats['completed_days'],
            delta=f"{stats['completed_days']/stats['total_days']*100:.0f}%" if stats['total_days'] > 0 else "0%",
            help="Days with 100% completion"
        )
    
    with col3:
        st.metric(
            "Avg. Completion",
            f"{stats['avg_completion']:.1f}%",
            help="Average completion percentage across all scheduled days"
        )
    
    with col4:
        completion_rate = (stats['total_topics_completed'] / stats['total_topics_scheduled'] * 100) if stats['total_topics_scheduled'] > 0 else 0
        st.metric(
            "Topics Done",
            f"{stats['total_topics_completed']}/{stats['total_topics_scheduled']}",
            delta=f"{completion_rate:.0f}%",
            help="Total topics completed out of scheduled"
        )


def show_daily_schedule(scheduler: StudyScheduler, schedule: DailySchedule, user_id: int):
    """Display a single day's schedule with interactive controls"""
    
    # Date header with completion status
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader(f"📆 {schedule.date.strftime('%A, %B %d, %Y')}")
    
    with col2:
        if schedule.completion_percentage >= 100:
            st.success("✅ Completed")
        elif schedule.completion_percentage > 0:
            st.info(f"⏳ {schedule.completion_percentage:.0f}%")
        else:
            st.warning("📝 Pending")
    
    # Total time for the day
    hours = schedule.total_minutes // 60
    minutes = schedule.total_minutes % 60
    st.caption(f"Total study time: **{hours}h {minutes}m**")
    
    if not schedule.items:
        st.info("No activities scheduled for this day. Click 'Regenerate Schedule' to create one.")
        return
    
    st.markdown("---")
    
    # Group items by activity type
    revision_items = [item for item in schedule.items if item.activity_type == 'revise']
    practice_items = [item for item in schedule.items if item.activity_type == 'practice']
    learn_items = [item for item in schedule.items if item.activity_type == 'learn']
    
    # Display sections
    if revision_items:
        st.markdown("### 🔄 Revision")
        for item in revision_items:
            show_schedule_item(scheduler, schedule.date, item, user_id)
    
    if practice_items:
        st.markdown("### 💪 Practice")
        for item in practice_items:
            show_schedule_item(scheduler, schedule.date, item, user_id)
    
    if learn_items:
        st.markdown("### 📚 Learn New Topics")
        for item in learn_items:
            show_schedule_item(scheduler, schedule.date, item, user_id)
    
    # Notes section
    st.markdown("---")
    st.markdown("### 📝 Notes")
    notes = st.text_area(
        "Add notes about today's study session",
        value=schedule.notes,
        key=f"notes_{schedule.date}",
        height=100,
        placeholder="How was your study session? Any challenges?"
    )
    
    if notes != schedule.notes:
        schedule.notes = notes
        scheduler.save_schedule(schedule)


def show_schedule_item(
    scheduler: StudyScheduler,
    schedule_date: date,
    item,
    user_id: int
):
    """Display a single schedule item with completion controls"""
    
    # Activity type icon and color
    icons = {
        'revise': '🔄',
        'practice': '💪',
        'learn': '📚'
    }
    
    colors = {
        'revise': '#FF6B6B',
        'practice': '#4ECDC4',
        'learn': '#45B7D1'
    }
    
    difficulty_colors = {
        'Easy': '🟢',
        'Medium': '🟡',
        'Hard': '🔴'
    }
    
    icon = icons.get(item.activity_type, '📖')
    color = colors.get(item.activity_type, '#95A5A6')
    
    # Card container
    with st.container():
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(
                f"""
                <div style="
                    padding: 15px;
                    border-left: 4px solid {color};
                    background-color: rgba(0,0,0,0.05);
                    border-radius: 5px;
                    margin-bottom: 10px;
                ">
                    <h4 style="margin: 0 0 8px 0;">
                        {icon} {item.topic_name}
                    </h4>
                    <p style="margin: 0; color: #666; font-size: 0.9em;">
                        <strong>{item.subject}</strong> • {difficulty_colors.get(item.difficulty, '')} {item.difficulty}
                    </p>
                    <p style="margin: 5px 0 0 0; font-size: 0.85em; color: #888;">
                        {item.reason}
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        with col2:
            st.markdown(f"**⏱️ {item.duration_minutes} min**")
        
        with col3:
            # Action buttons
            if item.activity_type == 'learn':
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("Start", key=f"start_{schedule_date}_{item.topic_id}", use_container_width=True):
                        # Navigate to learning page
                        st.session_state.selected_topic_id = item.topic_id
                        st.session_state.current_page = 'learn'
                        st.rerun()
                with col_b:
                    if st.button("✓ Done", key=f"done_learn_{schedule_date}_{item.topic_id}", use_container_width=True):
                        scheduler.mark_item_completed(schedule_date, item.topic_id)
                        st.success("Marked as completed!")
                        st.rerun()
            
            elif item.activity_type == 'practice':
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("Quiz", key=f"quiz_{schedule_date}_{item.topic_id}", use_container_width=True):
                        # Navigate to quiz page with this topic
                        st.session_state.selected_topics = [item.topic_id]
                        st.session_state.current_page = 'quiz'
                        st.rerun()
                with col_b:
                    if st.button("✓ Done", key=f"done_practice_{schedule_date}_{item.topic_id}", use_container_width=True):
                        scheduler.mark_item_completed(schedule_date, item.topic_id)
                        st.success("Marked as completed!")
                        st.rerun()
            
            elif item.activity_type == 'revise':
                # Revision quality rating
                with st.popover("✅ Done", use_container_width=True):
                    st.write("How well did you recall this topic?")
                    
                    quality = st.radio(
                        "Quality",
                        options=[5, 4, 3, 2, 1, 0],
                        format_func=lambda x: {
                            5: "⭐⭐⭐⭐⭐ Perfect recall",
                            4: "⭐⭐⭐⭐ Good, slight hesitation",
                            3: "⭐⭐⭐ Okay, some difficulty",
                            2: "⭐⭐ Poor, but remembered",
                            1: "⭐ Very poor, barely recalled",
                            0: "❌ Complete blackout"
                        }[x],
                        key=f"quality_{schedule_date}_{item.topic_id}",
                        label_visibility="collapsed"
                    )
                    
                    if st.button("Submit", key=f"submit_{schedule_date}_{item.topic_id}"):
                        scheduler.mark_item_completed(schedule_date, item.topic_id, quality)
                        st.success("Marked as completed!")
                        st.rerun()
        
        st.markdown("---")


if __name__ == "__main__":
    show_schedule_page()
