# Admin Panel Guide - Study Nation

## 🔐 Admin Panel Overview

The Study Nation Admin Panel is a secure interface for managing questions, courses, and study materials. This guide covers all features and usage instructions.

## ⚡ Quick Start

### Login Credentials (Default)

```
Username: admin
Password: admin123
```

### Access Admin Panel

- URL: `http://localhost:8000/admin-panel/login/`
- Sidebar Link: Click "🔐 Admin" in the main navigation

## 📊 Dashboard Features

The dashboard provides:

- **Statistics**: Total questions, courses, and CSV uploads
- **Quick Actions**: Buttons to CSV upload, manual entry, and manage questions
- **Recent Uploads**: List of latest CSV imports with success/failure status

## 📤 CSV Upload Feature

### Overview

Bulk import questions from a CSV file to quickly populate question banks.

### CSV File Format

Required columns:

```
question_text          - The question statement (required)
question_type          - Type of question (required)
option_a, option_b, option_c, option_d - Answer options
correct_answer         - The correct answer(s)
marks                  - Points for the question (default: 1)
explanation            - Optional explanation for the answer
```

### Question Types Supported

1. **single_choice** - Multiple choice with one correct answer
   - Options: A, B, C, or D
   - Example: `correct_answer=A`

2. **multiple_choice** - Multiple answers can be correct
   - Options: Comma-separated (A,B,C)
   - Example: `correct_answer=A,B,D`

3. **true_false** - True or False questions
   - Options: True or False
   - Example: `correct_answer=True`

4. **numerical** - Questions requiring numerical answers
   - Options: Leave empty
   - Example: `correct_answer=42`

5. **matching** - Matching column questions
   - Options: Can contain matching pairs
   - Example: `correct_answer=1-A;2-B;3-C`

### Sample CSV Data

```csv
question_text,question_type,option_a,option_b,option_c,option_d,correct_answer,marks,explanation
What is 2+2?,single_choice,1,2,3,4,D,1,The sum of 2 and 2 equals 4.
Is Python a language?,true_false,True,False,,,True,1,Yes Python is a programming language.
What is 15+27?,numerical,,,,,42,1,Simple addition: 15 + 27 = 42.
```

### Upload Steps

1. Go to **📤 Upload CSV** in sidebar
2. Select a **Course** from dropdown
3. Select a **Question Bank** from dropdown
4. Click on upload area or drag and drop CSV file
5. File automatically validates (max 5MB, .csv only)
6. Click **🚀 Upload and Process CSV**
7. System processes file and displays results:
   - ✅ Successful imports
   - ❌ Failed imports with error details

### Validation Rules

- Questions must have non-empty question_text
- Question type must be valid (see types above)
- Correct answer format must match question type
- Marks must be a positive integer
- File size limit: 5MB
- Maximum questions per upload: Unlimited

### Error Handling

If errors occur:

1. Check file format matches template
2. Verify all required columns present
3. Ensure no empty question texts
4. Validate correct_answer format
5. Check file encoding (UTF-8 recommended)

## ✏️ Manual Question Entry

### Overview

Add individual questions one at a time with a user-friendly form.

### Add Question Steps

1. Go to **➕ Add Question** in sidebar
2. Select a **Question Bank** from dropdown
3. Choose **Question Type**:
   - Single Choice
   - Multiple Choice
   - True/False
   - Numerical
   - Matching
4. Enter **Question Text** (required)
5. For choice questions:
   - Enter Option A, B, C, D
   - Specify correct answer (A/B/C/D or A,B for multiple)
6. Enter **Marks** (points awarded)
7. Add **Explanation** (optional but recommended)
8. Click **✅ Add Question**

### Question Type Variations

**Single Choice**

- Shows all 4 option fields
- Answer: Single letter (A, B, C, or D)

**Multiple Choice**

- Shows all 4 option fields
- Answer: Comma-separated letters (A,B,C)

**True/False**

- Shows basic True/False options
- Answer: True or False

**Numerical**

- No option fields shown
- Answer: Exact numerical value

**Matching**

- Option fields for pairs
- Answer: Format as 1-A;2-B;3-C

### Tips for Manual Entry

- Keep questions concise but clear
- Make options distinct and plausible
- Always provide explanation for learning
- Use consistent formatting
- Test questions before publishing

## ❓ Manage Questions

### Overview

View, search, and manage all questions in the system.

### Features

- **Filter by Question Bank**: Dropdown to filter questions
- **View Details**: See each question's metadata
- **Type Badge**: Visual indicator of question type
- **Marks Display**: Points for each question
- **Date Created**: When question was added
- **Correct Answer**: Quick reference to right answer

### Question Information Displayed

For each question:

- Question text (truncated to 20 words)
- Type badge (color-coded)
- Question bank it belongs to
- Points/marks
- Creation date
- Correct answer

### Filtering Questions

1. Select a question bank from dropdown
2. Click filter button (optional)
3. View filtered results
4. All questions from selected bank display

## 🔒 Security Features

### Authentication

- Username/password login required
- Session-based authentication
- CSRF protection on all forms
- Secure password storage (hashing)

### File Upload Security

- File type validation (CSV only)
- File size limit (5MB)
- Content validation before import
- Error logging and audit trail

### Access Control

- Admin role required
- Permission checks on all views
- Separate admin URLs protected
- Auto-redirect to login if not authenticated

### Data Protection

- All uploads logged with timestamp
- Admin user tracked for each upload
- Success/failure statistics maintained
- Error details saved for debugging

## 📊 Upload History

### View Upload Records

Dashboard shows:

- File name
- Total questions
- Successful imports
- Failed imports
- Upload status (Success/Partial/Failed)
- Upload date and time

### Status Meanings

- **Success**: All questions imported without errors
- **Partial**: Some questions imported, some failed
- **Failed**: No questions imported, critical error
- **Processing**: Currently being processed

### CSV Import Statistics

Track:

- Total uploads attempted
- Success rate percentage
- Common error patterns
- Upload trends over time

## 🎯 Best Practices

### CSV Preparation

1. Validate CSV in spreadsheet app first
2. Use UTF-8 encoding
3. Remove extra spaces/formatting
4. Check for special characters
5. Test with small file first

### Question Creation

1. Write clear, unambiguous questions
2. Ensure options are distinct
3. Always include explanations
4. Use consistent terminology
5. Review before publishing

### File Management

1. Keep backup copies
2. Name files descriptively (e.g., Python_Final_Exam_2024.csv)
3. Version control for updates
4. Document question sources
5. Track upload dates

### Admin Workflow

1. Review questions before bulk upload
2. Test manual entry first
3. Verify imports completed successfully
4. Check error logs for issues
5. Maintain audit trail

## 🆘 Troubleshooting

### Login Issues

- Clear browser cache and cookies
- Ensure correct username/password
- Check if admin user exists
- Verify database migrations applied

### CSV Upload Errors

- **File too large**: Reduce to under 5MB
- **Invalid format**: Check column headers
- **Empty questions**: Remove rows with no text
- **Wrong type**: Verify question_type is valid
- **Encoding issues**: Save as UTF-8

### Questions Not Appearing

- Verify import status shows success
- Check question bank was selected
- Refresh page after import
- Check database connection
- Review error logs

### Performance Issues

- Limit CSV to 1000 rows at a time
- Use manual entry for frequent updates
- Archive old question banks
- Clear upload history periodically

## 🔄 Admin Workflow Example

### Importing 100 Python Questions

1. **Prepare CSV**
   - Export from question database
   - Validate format (Python questions template)
   - Check all columns present

2. **Create Question Bank** (if needed)
   - Go to Django admin: /admin
   - Add new Question Bank
   - Name: "Python Advanced Quiz"
   - Course: "Advanced Python Programming"

3. **Upload CSV**
   - Click "📤 Upload CSV"
   - Select course and question bank
   - Upload CSV file
   - Review results

4. **Handle Failures**
   - Note error messages
   - Fix problematic rows
   - Re-upload corrected file
   - Or use manual entry for individual questions

5. **Verify Import**
   - Check dashboard statistics
   - View questions in manage section
   - Spot check random questions
   - Update course question count

## 📱 Mobile Access

The admin panel is responsive:

- Sidebar adapts on mobile
- Forms stack properly
- Buttons remain accessible
- Tables responsive with scrolling

Best experience on desktop for CSV uploads.

## 🔔 Notifications

- Success messages appear after actions
- Error messages highlight problems
- Import completion notices shown
- Status updates in dashboard

## 📚 Learning Resources

- Sample CSV: `sample_questions.csv`
- Setup script: `create_admin_user.py`
- Source code: `admin_panel/` directory
- Full documentation: This guide

## 🚀 Advanced Features

### Future Enhancements

- Question editing interface
- Batch question deletion
- Export questions to CSV
- Question analytics
- Performance statistics
- User activity logs

### Integration Points

- REST API for bulk operations
- Webhook support for integrations
- Third-party data sources
- Learning management system (LMS) sync

## 📞 Support

For issues:

1. Check this guide first
2. Review error messages
3. Check upload history
4. Review Django admin logs
5. Contact development team

## ✅ Checklist for Admins

Setup Checklist:

- [ ] Admin account created and login works
- [ ] CSV template downloaded and reviewed
- [ ] Test course and question bank created
- [ ] Sample CSV uploaded successfully
- [ ] Manual question creation tested
- [ ] Question filtering works
- [ ] Dashboard displays correctly

Daily Operations:

- [ ] Review new uploads
- [ ] Check import success rates
- [ ] Handle any errors from previous day
- [ ] Backup question database
- [ ] Monitor storage usage

Monthly Tasks:

- [ ] Archive old uploads
- [ ] Review and optimize question banks
- [ ] Analyze student performance data
- [ ] Update question bank descriptions
- [ ] Plan new question additions

---

**Version**: 1.0  
**Last Updated**: 2024  
**Admin Panel Version**: 1.0
