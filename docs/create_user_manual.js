/**
 * Study Nation User Manual generator (Student + Admin)
 * Requires: npm install docx
 */
const fs = require("fs");
const path = require("path");
const {
  Document,
  Packer,
  Paragraph,
  TextRun,
  ImageRun,
  HeadingLevel,
  AlignmentType,
  Header,
  Footer,
  PageNumber,
  BorderStyle,
  LevelFormat,
  PageBreak,
  TableOfContents,
  WidthType,
  Table,
  TableRow,
  TableCell,
  ShadingType,
} = require("docx");

const SHOT = path.join(__dirname, "manual_screenshots");
const OUT = path.join(__dirname, "Study_Nation_User_Manual.docx");

function img(name, width = 540, height = 325) {
  const file = path.join(SHOT, name);
  if (!fs.existsSync(file)) {
    console.warn("Missing screenshot:", name);
    return new Paragraph({
      children: [
        new TextRun({
          text: `[Screenshot not available: ${name}]`,
          italics: true,
          color: "888888",
          size: 20,
        }),
      ],
      spacing: { before: 120, after: 120 },
    });
  }
  const data = fs.readFileSync(file);
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 160, after: 80 },
    children: [
      new ImageRun({
        type: "png",
        data,
        transformation: { width, height },
        altText: {
          title: name,
          description: `Screenshot ${name}`,
          name: name,
        },
      }),
    ],
  });
}

function caption(text) {
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 200 },
    children: [
      new TextRun({
        text,
        italics: true,
        size: 18,
        color: "555555",
        font: "Arial",
      }),
    ],
  });
}

function p(text, opts = {}) {
  return new Paragraph({
    spacing: { after: 140, line: 276 },
    children: [
      new TextRun({
        text,
        font: "Arial",
        size: 22,
        ...opts,
      }),
    ],
  });
}

function bullet(text, ref = "bullets") {
  return new Paragraph({
    numbering: { reference: ref, level: 0 },
    spacing: { after: 80 },
    children: [new TextRun({ text, font: "Arial", size: 22 })],
  });
}

function num(text, ref = "steps") {
  return new Paragraph({
    numbering: { reference: ref, level: 0 },
    spacing: { after: 80 },
    children: [new TextRun({ text, font: "Arial", size: 22 })],
  });
}

function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 280, after: 160 },
    children: [new TextRun({ text, bold: true, font: "Arial", size: 32, color: "2F3B8C" })],
  });
}

function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 220, after: 120 },
    children: [new TextRun({ text, bold: true, font: "Arial", size: 26, color: "4A3FA0" })],
  });
}

function h3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 160, after: 100 },
    children: [new TextRun({ text, bold: true, font: "Arial", size: 24, color: "333333" })],
  });
}

function tip(text) {
  return new Paragraph({
    spacing: { before: 80, after: 140 },
    border: {
      left: { style: BorderStyle.SINGLE, size: 24, color: "667EEA", space: 8 },
    },
    indent: { left: 120 },
    children: [
      new TextRun({ text: "Tip: ", bold: true, font: "Arial", size: 20, color: "4A3FA0" }),
      new TextRun({ text, font: "Arial", size: 20, color: "333333" }),
    ],
  });
}

function noteFixed(text) {
  return new Paragraph({
    spacing: { before: 80, after: 140 },
    border: {
      left: { style: BorderStyle.SINGLE, size: 24, color: "E6A23C", space: 8 },
    },
    indent: { left: 120 },
    children: [
      new TextRun({ text: "Note: ", bold: true, font: "Arial", size: 20, color: "B8821A" }),
      new TextRun({ text, font: "Arial", size: 20 }),
    ],
  });
}

const thin = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: thin, bottom: thin, left: thin, right: thin };

function cell(text, width, opts = {}) {
  return new TableCell({
    borders,
    width: { size: width, type: WidthType.DXA },
    shading: opts.fill
      ? { fill: opts.fill, type: ShadingType.CLEAR }
      : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [
      new Paragraph({
        children: [
          new TextRun({
            text,
            bold: !!opts.bold,
            font: "Arial",
            size: opts.size || 18,
            color: opts.color || "333333",
          }),
        ],
      }),
    ],
  });
}

function simpleTable(headers, rows, widths) {
  const total = widths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: widths,
    rows: [
      new TableRow({
        children: headers.map((h, i) =>
          cell(h, widths[i], { bold: true, fill: "EEF0FB", color: "2F3B8C" })
        ),
      }),
      ...rows.map(
        (r) =>
          new TableRow({
            children: r.map((c, i) => cell(c, widths[i])),
          })
      ),
    ],
  });
}

async function main() {
  const children = [];

  // Cover
  children.push(
    new Paragraph({ spacing: { before: 1200 } , children: [] }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [
        new TextRun({
          text: "STUDY NATION",
          bold: true,
          font: "Arial",
          size: 48,
          color: "5A52C2",
        }),
      ],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 200, after: 200 },
      children: [
        new TextRun({
          text: "User Manual",
          bold: true,
          font: "Arial",
          size: 40,
          color: "222222",
        }),
      ],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 120 },
      children: [
        new TextRun({
          text: "Student View  ·  Admin View",
          font: "Arial",
          size: 26,
          color: "555555",
        }),
      ],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 400 },
      children: [
        new TextRun({
          text: "A practical guide to using the Study Nation web application",
          font: "Arial",
          size: 22,
          italics: true,
          color: "666666",
        }),
      ],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 600 },
      children: [
        new TextRun({
          text: `Version 1.0  ·  ${new Date().toLocaleDateString("en-GB", {
            year: "numeric",
            month: "long",
            day: "numeric",
          })}`,
          font: "Arial",
          size: 20,
          color: "888888",
        }),
      ],
    }),
    new Paragraph({ children: [new PageBreak()] }),

    // TOC
    h1("Table of Contents"),
    new TableOfContents("Table of Contents", {
      hyperlink: true,
      headingStyleRange: "1-2",
    }),
    new Paragraph({ children: [new PageBreak()] }),

    // Intro
    h1("1. Introduction"),
    p(
      "Study Nation is an online learning platform where students can browse courses, study resources, build practice exams from past papers, take timed practice quizzes, join public discussion boards, and read blogs. Administrators manage all educational content through a secure Admin Panel."
    ),
    h2("1.1 Who this manual is for"),
    bullet("Students and learners — account signup, study materials, exams, chat."),
    bullet("Administrators / teachers — categories, courses, questions, exams, blogs."),
    h2("1.2 What you need"),
    bullet("A modern web browser (Chrome, Edge, Firefox, or Safari)."),
    bullet("Internet access to your Study Nation website address."),
    bullet("For students: a free account (Sign Up)."),
    bullet("For admins: credentials provided by your organization."),
    h2("1.3 Main areas of the site"),
    simpleTable(
      ["Area", "Who uses it", "Purpose"],
      [
        ["Public website", "Everyone", "Home, courses, resources, blogs, contact"],
        ["Student account", "Students", "My Exams, My Lists, practice quizzes, chat posts"],
        ["Admin Panel", "Admins only", "Manage content, questions, exams, blogs"],
      ],
      [2800, 2600, 3960]
    ),
    new Paragraph({ spacing: { after: 200 }, children: [] }),
    img("01_home.png"),
    caption("Figure 1 — Home page of Study Nation"),

    // Getting started
    h1("2. Getting Started (Everyone)"),
    h2("2.1 Open the website"),
    num("Open your browser and go to the Study Nation URL (for local setup: http://127.0.0.1:8000/).", "gs"),
    num("You will see the Home page with the main navigation bar at the top.", "gs"),
    h2("2.2 Navigation bar"),
    p("The top menu is available on most public pages:"),
    bullet("Home — landing page and featured categories."),
    bullet("Courses — browse all courses and open a course detail page."),
    bullet("Past Papers — practice materials; also links to My Exams (when logged in) and Public Chat."),
    bullet("Resources — free and paid study resources."),
    bullet("Blogs — articles and updates."),
    bullet("Contact — send a message to the support team."),
    bullet("Log In / Sign Up — student account access."),
    bullet("Admin — opens the Admin Panel login (staff only)."),

    // STUDENT SECTION
    h1("3. Student Guide"),
    h2("3.1 Create a student account"),
    num("Click Sign Up in the top navigation.", "s1"),
    num("Enter your full name, username, email, and a strong password (at least 8 characters).", "s1"),
    num("Click Create account (or the submit button on the form).", "s1"),
    num("You are logged in automatically and taken to My Exams.", "s1"),
    img("02_student_signup.png"),
    caption("Figure 2 — Student Sign Up page"),
    tip("Use a real email you can access. Usernames and emails must be unique."),

    h2("3.2 Log in as a student"),
    num("Click Log In.", "s2"),
    num("Enter your username or email and password.", "s2"),
    num("Click Log in. You will land on My Exams (or the page you were trying to open).", "s2"),
    img("03_student_login.png"),
    caption("Figure 3 — Student Log In page"),
    p("After login, the menu also shows My Lists and Log Out."),

    h2("3.3 Browse courses"),
    num("Click Courses in the top menu.", "s3"),
    num("Browse the course cards. Open a course to see description, materials, and related questions when available.", "s3"),
    img("04_courses.png"),
    caption("Figure 4 — Courses list"),

    h2("3.4 Use resources"),
    num("Click Resources.", "s4"),
    num("View free resources and paid resource listings.", "s4"),
    num("Open a resource to read its details and view the attached file (when available).", "s4"),
    img("05_resources.png"),
    caption("Figure 5 — Resources page"),

    h2("3.5 Read blogs"),
    num("Click Blogs to see published articles.", "s5"),
    num("Open any post to read the full content and attachments (PDF, video, etc.).", "s5"),
    img("06_blogs.png"),
    caption("Figure 6 — Blogs list"),

    h2("3.6 Past papers overview"),
    p(
      "Past Papers is the study hub for exam-style practice. From here you can learn about the feature and jump into building your own practice exams (after login)."
    ),
    img("07_past_papers.png"),
    caption("Figure 7 — Past Papers page"),

    h2("3.7 My Exams — build a practice exam"),
    p(
      "My Exams lets you create personal practice exams by selecting questions from the question bank (past-paper style questions with paper codes)."
    ),
    num("Go to Past Papers → My Exams, or open /my-exams/ after login.", "s6"),
    num("Click Create / New Exam. A draft exam is created and the Exam Builder opens.", "s6"),
    num("Use filters (Category / Type, Topic, Year) and click Submit to find questions.", "s6"),
    num("Add questions to your exam using the + control on each question row.", "s6"),
    num("Open Selected Questions to reorder items if needed.", "s6"),
    num("Open Settings to rename the exam, set duration, and save options.", "s6"),
    img("10_student_my_exams.png"),
    caption("Figure 8 — My Exams list"),
    img("11_student_exam_builder.png"),
    caption("Figure 9 — Student Exam Builder"),
    tip("Only questions with paper codes appear in the Exam Builder filters — these are typically imported past-paper questions."),

    h2("3.8 Practice this exam (timed quiz)"),
    num("From My Exams or the exam builder, start Practice.", "s7"),
    num("Answer multiple-choice questions by selecting letters; type answers for numerical / structured questions.", "s7"),
    num("Submit the exam when finished. You will see your score, correct / wrong / unanswered counts, and a review of each question.", "s7"),
    noteFixed(
      "Auto-grading is exact for choice questions. Free-text answers are graded with best-effort text matching."
    ),

    h2("3.9 My Lists — build a question list"),
    p(
      "Question lists are personal collections of questions (similar to exams, but focused on organizing questions rather than timed practice)."
    ),
    num("Open My Lists from the top menu.", "s8"),
    num("Create a new list and add questions with filters, the same way as the exam builder.", "s8"),
    img("12_student_my_lists.png"),
    caption("Figure 10 — My Lists"),
    img("12b_student_list_builder.png"),
    caption("Figure 11 — Question list builder"),

    h2("3.10 Public Chat (discussion boards)"),
    p(
      "Public Chat is a community Q&A space organized into discussion boards (topics). Anyone can read; posting requires login."
    ),
    num("Open Past Papers → Public Chat (or /public-chat/).", "s9"),
    num("Select a board from the left sidebar.", "s9"),
    num("Click Create Post, enter a title and details, optionally attach an image, then Post.", "s9"),
    num("Open a post and write a comment/reply. You can edit or delete your own replies.", "s9"),
    img("08_public_chat.png"),
    caption("Figure 12 — Public Chat"),
    tip("Use the ∑ Math Type button to insert equations in titles and posts."),

    h2("3.11 Contact support"),
    num("Open Contact.", "s10"),
    num("Fill name, email, subject, category, and message.", "s10"),
    num("Click Send Message. Your message is saved for the support team.", "s10"),
    img("09_contact.png"),
    caption("Figure 13 — Contact form"),

    h2("3.12 Log out"),
    p("Click Log Out in the navigation bar when you finish. This protects your account on shared computers."),

    // ADMIN SECTION
    h1("4. Admin Guide"),
    p(
      "The Admin Panel is separate from the student site. Only users with an admin profile can access it. Students cannot open admin pages even if they know the URL."
    ),
    h2("4.1 Admin login"),
    num("Click Admin in the public navigation, or open /admin-panel/login/.", "a1"),
    num("Enter your admin username and password.", "a1"),
    num("On success you reach the Dashboard.", "a1"),
    img("13_admin_login.png"),
    caption("Figure 14 — Admin login"),
    noteFixed("Use the credentials issued by your system administrator. Do not share admin accounts."),

    h2("4.2 Dashboard"),
    p("The dashboard shows quick counts (questions, courses, blogs, uploads) and recent activity."),
    img("14_admin_dashboard.png"),
    caption("Figure 15 — Admin dashboard"),
    p("The left sidebar is your main menu. Sections are ordered by dependency:"),
    bullet("Setup — Categories → Courses → Resources"),
    bullet("Questions — Upload → Add → Manage"),
    bullet("Assessments — Exam Builder → Question Lists"),
    bullet("Content — Blogs"),

    h2("4.3 Manage Categories"),
    p("Categories group courses (for example JEE, Class 10, Mathematics). Create categories before courses."),
    num("Open Manage Categories.", "a2"),
    num("Create a category with name and optional description.", "a2"),
    num("Edit or delete categories carefully (courses may depend on them).", "a2"),
    img("15_admin_categories.png"),
    caption("Figure 16 — Manage Categories"),

    h2("4.4 Manage Courses"),
    num("Open Manage Courses.", "a3"),
    num("Create a course: title, description, category, level, thumbnail, curriculum, etc.", "a3"),
    num("Edit existing courses to keep content up to date.", "a3"),
    img("16_admin_courses.png"),
    caption("Figure 17 — Manage Courses"),

    h2("4.5 Manage Resources"),
    p("Upload study files (notes, e-books, worksheets) and mark them free or paid."),
    img("17_admin_resources.png"),
    caption("Figure 18 — Manage Resources"),

    h2("4.6 Upload Questions (CSV / Excel / Word)"),
    p(
      "Bulk import is the fastest way to load past-paper questions. Supported formats: CSV, Excel (.xlsx/.xls), and Word (.docx)."
    ),
    num("Open Upload Questions.", "a4"),
    num("Select the target question bank / course.", "a4"),
    num("For Word imports, enter paper code (required so questions appear in Exam Builder).", "a4"),
    num("Optionally set year, season, and zone for past-paper metadata.", "a4"),
    num("Upload the file and review the success / failure summary.", "a4"),
    num("Open Manage Questions to verify imported items.", "a4"),
    img("18_admin_upload_questions.png"),
    caption("Figure 19 — Upload Questions"),
    tip("Use the Sample Template / Sample DOCX download buttons on the upload page for the correct format."),

    h2("4.7 Add Question (wizard)"),
    p("Create questions one-by-one or in bulk using the question wizard."),
    num("Open Add Question.", "a5"),
    num("Choose question type (MCQ, true/false, numerical, structured, etc.).", "a5"),
    num("Enter question text, options, correct answer, marks, and solution.", "a5"),
    num("Use the math / equation tools when formulas are needed.", "a5"),
    num("Save the question into the selected bank.", "a5"),
    img("19_admin_add_question.png"),
    caption("Figure 20 — Add Question wizard"),

    h2("4.8 Manage Questions"),
    p("Search and filter the full question bank. Edit answers, solutions, and metadata."),
    img("20_admin_manage_questions.png"),
    caption("Figure 21 — Manage Questions"),

    h2("4.9 Exam Builder (admin)"),
    p(
      "Admin Exam Builder creates curated exams for the organization. The workflow matches the student builder but is managed from the admin side."
    ),
    num("Open Exam Builder → create a new exam or open an existing one.", "a6"),
    num("Filter questions by topic, year, and category.", "a6"),
    num("Add questions, reorder them, and configure settings.", "a6"),
    img("21_admin_exams.png"),
    caption("Figure 22 — Exam list"),
    img("22_admin_exam_builder.png"),
    caption("Figure 23 — Admin Exam Builder"),

    h2("4.10 Build Question List (admin)"),
    p("Curated question lists can be maintained for teaching or publishing sets of questions."),
    img("23_admin_question_lists.png"),
    caption("Figure 24 — Admin question lists"),

    h2("4.11 Manage Blogs"),
    num("Open Manage Blogs.", "a7"),
    num("Create a post with title, content, optional image, video, PDF, or PPT.", "a7"),
    num("Publish or unpublish as needed. Edit or delete posts from the list.", "a7"),
    img("24_admin_blogs.png"),
    caption("Figure 25 — Manage Blogs"),

    h2("4.12 Logout"),
    p("Use Logout at the bottom of the admin sidebar when finished."),

    // Recommended workflow
    h1("5. Recommended Admin Workflow"),
    p("Follow this order when setting up a new subject area:"),
    num("Create Categories.", "wf"),
    num("Create Courses under those categories.", "wf"),
    num("Create Question Banks (via course / upload flow) and Upload Questions.", "wf"),
    num("Review questions in Manage Questions.", "wf"),
    num("Build Exams and Question Lists for practice.", "wf"),
    num("Add Resources and Blogs for study support.", "wf"),

    // FAQ
    h1("6. Tips & Troubleshooting"),
    h2("6.1 Student issues"),
    bullet("Cannot see My Exams — log in with a student account (not admin)."),
    bullet("No questions in Exam Builder — filters may be too narrow, or questions lack paper_code."),
    bullet("Forgot password — ask admin to reset your account (self-service reset may not be enabled)."),
    bullet("Math looks wrong in chat — use ∑ Math Type and keep formulas inside $...$ when needed."),
    h2("6.2 Admin issues"),
    bullet("Login fails with “not an admin user” — your user needs an Admin Profile."),
    bullet("Word import succeeds but questions missing in builder — paper code was empty."),
    bullet("Delete buttons do nothing with a plain link — deletes use POST; use the Delete button on the form."),
    bullet("Students must not share admin credentials."),

    // Glossary
    h1("7. Glossary"),
    simpleTable(
      ["Term", "Meaning"],
      [
        ["Question Bank", "A collection of questions, usually linked to a course."],
        ["Paper code", "Past-paper identifier (for example 0606/23). Needed for Exam Builder lists."],
        ["Exam Builder", "Tool to select questions into a practice or curated exam."],
        ["Public Chat", "Discussion boards for community questions and answers."],
        ["Admin Profile", "Flag that allows a user into the Admin Panel."],
      ],
      [2800, 6560]
    ),

    new Paragraph({ spacing: { before: 400 }, children: [] }),
    p(
      "End of User Manual — Study Nation. For further help, use the Contact form or email support@studynation.com."
    )
  );

  const doc = new Document({
    styles: {
      default: {
        document: {
          run: { font: "Arial", size: 22 },
        },
      },
      paragraphStyles: [
        {
          id: "Heading1",
          name: "Heading 1",
          basedOn: "Normal",
          next: "Normal",
          quickFormat: true,
          run: { size: 32, bold: true, font: "Arial", color: "2F3B8C" },
          paragraph: { spacing: { before: 280, after: 160 }, outlineLevel: 0 },
        },
        {
          id: "Heading2",
          name: "Heading 2",
          basedOn: "Normal",
          next: "Normal",
          quickFormat: true,
          run: { size: 26, bold: true, font: "Arial", color: "4A3FA0" },
          paragraph: { spacing: { before: 220, after: 120 }, outlineLevel: 1 },
        },
        {
          id: "Heading3",
          name: "Heading 3",
          basedOn: "Normal",
          next: "Normal",
          quickFormat: true,
          run: { size: 24, bold: true, font: "Arial", color: "333333" },
          paragraph: { spacing: { before: 160, after: 100 }, outlineLevel: 2 },
        },
      ],
    },
    numbering: {
      config: [
        {
          reference: "bullets",
          levels: [
            {
              level: 0,
              format: LevelFormat.BULLET,
              text: "•",
              alignment: AlignmentType.LEFT,
              style: { paragraph: { indent: { left: 720, hanging: 360 } } },
            },
          ],
        },
        {
          reference: "gs",
          levels: [
            {
              level: 0,
              format: LevelFormat.DECIMAL,
              text: "%1.",
              alignment: AlignmentType.LEFT,
              style: { paragraph: { indent: { left: 720, hanging: 360 } } },
            },
          ],
        },
        {
          reference: "s1",
          levels: [
            {
              level: 0,
              format: LevelFormat.DECIMAL,
              text: "%1.",
              alignment: AlignmentType.LEFT,
              style: { paragraph: { indent: { left: 720, hanging: 360 } } },
            },
          ],
        },
        {
          reference: "s2",
          levels: [
            {
              level: 0,
              format: LevelFormat.DECIMAL,
              text: "%1.",
              alignment: AlignmentType.LEFT,
              style: { paragraph: { indent: { left: 720, hanging: 360 } } },
            },
          ],
        },
        {
          reference: "s3",
          levels: [
            {
              level: 0,
              format: LevelFormat.DECIMAL,
              text: "%1.",
              alignment: AlignmentType.LEFT,
              style: { paragraph: { indent: { left: 720, hanging: 360 } } },
            },
          ],
        },
        {
          reference: "s4",
          levels: [
            {
              level: 0,
              format: LevelFormat.DECIMAL,
              text: "%1.",
              alignment: AlignmentType.LEFT,
              style: { paragraph: { indent: { left: 720, hanging: 360 } } },
            },
          ],
        },
        {
          reference: "s5",
          levels: [
            {
              level: 0,
              format: LevelFormat.DECIMAL,
              text: "%1.",
              alignment: AlignmentType.LEFT,
              style: { paragraph: { indent: { left: 720, hanging: 360 } } },
            },
          ],
        },
        {
          reference: "s6",
          levels: [
            {
              level: 0,
              format: LevelFormat.DECIMAL,
              text: "%1.",
              alignment: AlignmentType.LEFT,
              style: { paragraph: { indent: { left: 720, hanging: 360 } } },
            },
          ],
        },
        {
          reference: "s7",
          levels: [
            {
              level: 0,
              format: LevelFormat.DECIMAL,
              text: "%1.",
              alignment: AlignmentType.LEFT,
              style: { paragraph: { indent: { left: 720, hanging: 360 } } },
            },
          ],
        },
        {
          reference: "s8",
          levels: [
            {
              level: 0,
              format: LevelFormat.DECIMAL,
              text: "%1.",
              alignment: AlignmentType.LEFT,
              style: { paragraph: { indent: { left: 720, hanging: 360 } } },
            },
          ],
        },
        {
          reference: "s9",
          levels: [
            {
              level: 0,
              format: LevelFormat.DECIMAL,
              text: "%1.",
              alignment: AlignmentType.LEFT,
              style: { paragraph: { indent: { left: 720, hanging: 360 } } },
            },
          ],
        },
        {
          reference: "s10",
          levels: [
            {
              level: 0,
              format: LevelFormat.DECIMAL,
              text: "%1.",
              alignment: AlignmentType.LEFT,
              style: { paragraph: { indent: { left: 720, hanging: 360 } } },
            },
          ],
        },
        {
          reference: "a1",
          levels: [
            {
              level: 0,
              format: LevelFormat.DECIMAL,
              text: "%1.",
              alignment: AlignmentType.LEFT,
              style: { paragraph: { indent: { left: 720, hanging: 360 } } },
            },
          ],
        },
        {
          reference: "a2",
          levels: [
            {
              level: 0,
              format: LevelFormat.DECIMAL,
              text: "%1.",
              alignment: AlignmentType.LEFT,
              style: { paragraph: { indent: { left: 720, hanging: 360 } } },
            },
          ],
        },
        {
          reference: "a3",
          levels: [
            {
              level: 0,
              format: LevelFormat.DECIMAL,
              text: "%1.",
              alignment: AlignmentType.LEFT,
              style: { paragraph: { indent: { left: 720, hanging: 360 } } },
            },
          ],
        },
        {
          reference: "a4",
          levels: [
            {
              level: 0,
              format: LevelFormat.DECIMAL,
              text: "%1.",
              alignment: AlignmentType.LEFT,
              style: { paragraph: { indent: { left: 720, hanging: 360 } } },
            },
          ],
        },
        {
          reference: "a5",
          levels: [
            {
              level: 0,
              format: LevelFormat.DECIMAL,
              text: "%1.",
              alignment: AlignmentType.LEFT,
              style: { paragraph: { indent: { left: 720, hanging: 360 } } },
            },
          ],
        },
        {
          reference: "a6",
          levels: [
            {
              level: 0,
              format: LevelFormat.DECIMAL,
              text: "%1.",
              alignment: AlignmentType.LEFT,
              style: { paragraph: { indent: { left: 720, hanging: 360 } } },
            },
          ],
        },
        {
          reference: "a7",
          levels: [
            {
              level: 0,
              format: LevelFormat.DECIMAL,
              text: "%1.",
              alignment: AlignmentType.LEFT,
              style: { paragraph: { indent: { left: 720, hanging: 360 } } },
            },
          ],
        },
        {
          reference: "wf",
          levels: [
            {
              level: 0,
              format: LevelFormat.DECIMAL,
              text: "%1.",
              alignment: AlignmentType.LEFT,
              style: { paragraph: { indent: { left: 720, hanging: 360 } } },
            },
          ],
        },
        {
          reference: "steps",
          levels: [
            {
              level: 0,
              format: LevelFormat.DECIMAL,
              text: "%1.",
              alignment: AlignmentType.LEFT,
              style: { paragraph: { indent: { left: 720, hanging: 360 } } },
            },
          ],
        },
      ],
    },
    sections: [
      {
        properties: {
          page: {
            size: { width: 12240, height: 15840 },
            margin: { top: 1008, right: 1008, bottom: 1008, left: 1008 },
          },
        },
        headers: {
          default: new Header({
            children: [
              new Paragraph({
                border: {
                  bottom: {
                    style: BorderStyle.SINGLE,
                    size: 6,
                    color: "667EEA",
                    space: 4,
                  },
                },
                spacing: { after: 120 },
                children: [
                  new TextRun({
                    text: "Study Nation — User Manual",
                    font: "Arial",
                    size: 16,
                    color: "5A52C2",
                  }),
                  new TextRun({
                    text: "\tStudent & Admin Guide",
                    font: "Arial",
                    size: 16,
                    color: "888888",
                  }),
                ],
                tabStops: [
                  {
                    type: "right",
                    position: 10080,
                  },
                ],
              }),
            ],
          }),
        },
        footers: {
          default: new Footer({
            children: [
              new Paragraph({
                alignment: AlignmentType.CENTER,
                border: {
                  top: {
                    style: BorderStyle.SINGLE,
                    size: 4,
                    color: "CCCCCC",
                    space: 6,
                  },
                },
                children: [
                  new TextRun({
                    text: "Page ",
                    font: "Arial",
                    size: 16,
                    color: "666666",
                  }),
                  new TextRun({
                    children: [PageNumber.CURRENT],
                    font: "Arial",
                    size: 16,
                    color: "666666",
                  }),
                  new TextRun({
                    text: " of ",
                    font: "Arial",
                    size: 16,
                    color: "666666",
                  }),
                  new TextRun({
                    children: [PageNumber.TOTAL_PAGES],
                    font: "Arial",
                    size: 16,
                    color: "666666",
                  }),
                ],
              }),
            ],
          }),
        },
        children,
      },
    ],
  });

  const buffer = await Packer.toBuffer(doc);
  fs.writeFileSync(OUT, buffer);
  console.log("Wrote", OUT);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
