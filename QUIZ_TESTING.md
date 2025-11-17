# Quiz System Testing Guide

## Quick Test Checklist

### 1. Quiz Generation Test
1. Navigate to Practice page (✍️ Practice button)
2. Select 1-2 topics from different subjects
3. Set question count to 5-10
4. Choose difficulty: Medium or Adaptive
5. Select at least 2 question types (e.g., MCQ + Numeric)
6. Click "🎯 Generate Quiz"
7. **Expected**: Quiz generates within 5-10 seconds, shows success message

### 2. Quiz Taking Test
1. **Timer Check**: Verify timer shows remaining time and counts down
2. **MCQ Questions**: Test radio button selection
3. **Numeric Questions**: Test number input field
4. **Descriptive Questions** (if included): Test text area input
5. Answer at least half the questions
6. Click "📝 Submit Quiz"
7. **Expected**: Submission succeeds within 3-5 seconds

### 3. Quiz Grading Test
1. Wait for grading to complete
2. **Expected Results**:
   - Total score displayed (e.g., 15/20)
   - Percentage calculated correctly
   - Correct count shown (e.g., 3/5)
   - Time taken displayed
   - Performance indicator shown (Excellent/Good/Review)

### 4. Results Display Test
1. Verify question-wise breakdown shows all questions
2. Check ✅ or ❌ indicators for each question
3. Expand wrong answers to see feedback
4. Verify correct answers shown for wrong responses
5. Test navigation buttons:
   - "🔄 Try Another Quiz" → Returns to topic selection
   - "📚 Review Topics" → Goes to Learn page
   - "📊 View Dashboard" → Goes to Dashboard

### 5. Edge Cases to Test
- [ ] Submit quiz with all questions unanswered
- [ ] Submit quiz with partial answers
- [ ] Select single topic
- [ ] Select all topics from one subject
- [ ] Generate quiz with only MCQ
- [ ] Generate quiz with only Descriptive
- [ ] Test adaptive difficulty with no prior attempts
- [ ] Generate 30-question quiz (max)
- [ ] Let timer run out (if time allows)

## Expected Behavior

### Question Generation
- **MCQ**: Should have 4 options (A, B, C, D)
- **Numeric**: Should expect numerical answer
- **Descriptive**: Should have detailed text area

### Grading Rules
- **MCQ**: Exact match required (case-insensitive)
- **Numeric**: Partial credit if within 0.5% tolerance
- **Descriptive**: LLM-based scoring with feedback

### Time Limits
- MCQ: 2 minutes per question
- Numeric: 3 minutes per question
- Descriptive: 5 minutes per question

### Adaptive Difficulty
- No prior attempts: Defaults to Medium
- Low mastery (<0.3): Easy
- Medium mastery (0.3-0.6): Medium
- High mastery (>0.6): Hard

## Database Verification

After taking a quiz, check database:

```bash
sqlite3 mindmentor.db
```

```sql
-- Check quiz was saved
SELECT * FROM quizzes ORDER BY created_at DESC LIMIT 1;

-- Check questions were saved
SELECT id, question_type, marks FROM questions 
WHERE quiz_id = (SELECT id FROM quizzes ORDER BY created_at DESC LIMIT 1);

-- Check quiz attempt was saved
SELECT * FROM quiz_attempts ORDER BY attempted_at DESC LIMIT 1;
```

## Known Limitations

1. **Timer is client-side**: Refreshing page resets timer
2. **Session state lost on refresh**: Quiz progress not persisted across page refresh
3. **Descriptive grading**: May take 5-10 seconds due to LLM call
4. **Cache warmup**: First quiz generation may take longer

## Troubleshooting

### Quiz Generation Fails
- Check `GEMINI_API_KEY` in .env
- Verify topics exist in database
- Check console for error messages

### Grading Takes Too Long
- Check network connection
- Descriptive questions use LLM (slower)
- Consider reducing descriptive question count

### Results Not Showing
- Check browser console for JavaScript errors
- Verify quiz_id was saved
- Check database connection

### Questions Displayed Incorrectly
- MCQ options should be formatted as "A. Option text"
- Check question generation prompts if format is wrong
- Verify JSON parsing in quiz_generator.py

## Performance Expectations

- **Quiz Generation**: 5-10 seconds for 10 questions
- **Grading (no descriptive)**: <2 seconds
- **Grading (with descriptive)**: 5-15 seconds depending on count
- **Cache Hit Rate**: Should be 60-80% after a few quizzes
- **Page Load**: <1 second for all pages

## Next Steps After Testing

1. If quiz system works:
   - Consider adding analytics to dashboard
   - Build study scheduler
   - Add more question templates

2. If issues found:
   - Document specific errors
   - Check logs and console output
   - Review grading logic for accuracy

3. Enhancements to consider:
   - Question difficulty indicators
   - Time-based scoring
   - Review wrong answers feature
   - Quiz history page
   - Export results as PDF
