import React, { useState, useMemo } from 'react';
import { 
  Trash2, 
  HelpCircle, 
  Users, 
  CheckCircle, 
  ListFilter, 
  PlusCircle, 
  RefreshCw,
  SlidersHorizontal
} from 'lucide-react';

// --- INITIAL MOCK DATA ---
const INITIAL_QUESTIONS = [
  { id: 'Q101', question: 'What is the time complexity of QuickSort average case?', topic: 'Algorithms', difficulty: 'Medium' },
  { id: 'Q102', question: 'What is a self-balancing binary search tree?', topic: 'Data Structures', difficulty: 'Hard' },
  { id: 'Q103', question: 'Explain the concept of Virtual Memory.', topic: 'Operating Systems', difficulty: 'Medium' },
  { id: 'Q104', question: 'What does SQL stand for?', topic: 'Databases', difficulty: 'Easy' },
  { id: 'Q105', question: 'Define the ACID properties in database transactions.', topic: 'Databases', difficulty: 'Medium' },
  { id: 'Q106', question: 'What is Dijkstra’s Algorithm used for?', topic: 'Algorithms', difficulty: 'Hard' },
  { id: 'Q107', question: 'What is the difference between Process and Thread?', topic: 'Operating Systems', difficulty: 'Easy' },
];

const INITIAL_STUDENTS = Array.from({ length: 30 }, (_, index) => ({
  rollNo: 101 + index,
  name: [
    'Alice Smith', 'Bob Johnson', 'Charlie Brown', 'David Miller', 'Emma Wilson',
    'Frank Thomas', 'Grace Lee', 'Hannah White', 'Ian Clark', 'Julia Lewis',
    'Kevin Hall', 'Laura Young', 'Michael King', 'Nina Wright', 'Oscar Scott',
    'Paul Green', 'Quinn Adams', 'Rachel Baker', 'Sam Gonzalez', 'Tina Nelson',
    'Ulysses Carter', 'Victoria Mitchell', 'Will Perez', 'Xena Roberts', 'Yusuf Turner',
    'Zoe Phillips', 'Aaron Campbell', 'Bella Parker', 'Caleb Evans', 'Diana Edwards'
  ][index]
}));

export default function App() {
  const [activeTab, setActiveTab] = useState('question-bank');

  // --- QUESTION BANK STATE ---
  const [questions, setQuestions] = useState(INITIAL_QUESTIONS);
  const [selectedTopics, setSelectedTopics] = useState('All');
  const [selectedDifficulty, setSelectedDifficulty] = useState('All');
  const [selectedQuestionIds, setSelectedQuestionIds] = useState([]);
  const [quizNotice, setQuizNotice] = useState('');

  // --- ROSTER STATE ---
  const [students] = useState(INITIAL_STUDENTS);
  const [groupName, setGroupName] = useState('');
  const [selectedStudentRolls, setSelectedStudentRolls] = useState([]);
  const [startRoll, setStartRoll] = useState('');
  const [endRoll, setEndRoll] = useState('');
  const [groups, setGroups] = useState([]);
  const [groupNotice, setGroupNotice] = useState('');

  // -------------------------------------------------------------
  // QUESTION BANK HANDLERS
  // -------------------------------------------------------------
  const filteredQuestions = useMemo(() => {
    return questions.filter((q) => {
      const matchTopic = selectedTopics === 'All' || q.topic === selectedTopics;
      const matchDiff = selectedDifficulty === 'All' || q.difficulty === selectedDifficulty;
      return matchTopic && matchDiff;
    });
  }, [questions, selectedTopics, selectedDifficulty]);

  const toggleSelectAllQuestions = (e) => {
    if (e.target.checked) {
      setSelectedQuestionIds(filteredQuestions.map((q) => q.id));
    } else {
      setSelectedQuestionIds([]);
    }
  };

  const toggleQuestionSelect = (id) => {
    setSelectedQuestionIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const handleDeleteSelectedQuestions = () => {
    if (selectedQuestionIds.length === 0) return;
    const confirmDelete = window.confirm(
      `Are you sure you want to delete ${selectedQuestionIds.length} selected question(s)?`
    );
    if (confirmDelete) {
      setQuestions((prev) => prev.filter((q) => !selectedQuestionIds.includes(q.id)));
      setSelectedQuestionIds([]);
      setQuizNotice(`Deleted ${selectedQuestionIds.length} question(s) successfully.`);
      setTimeout(() => setQuizNotice(''), 3000);
    }
  };

  const handleCreateLiveQuiz = () => {
    if (selectedQuestionIds.length === 0) return;
    setQuizNotice(`Live Quiz created with ${selectedQuestionIds.length} question(s)!`);
    setTimeout(() => setQuizNotice(''), 3000);
  };

  // -------------------------------------------------------------
  // CLASSROOM ROSTER HANDLERS
  // -------------------------------------------------------------
  const toggleStudentSelect = (rollNo) => {
    setSelectedStudentRolls((prev) =>
      prev.includes(rollNo) ? prev.filter((r) => r !== rollNo) : [...prev, rollNo]
    );
  };

  const handleApplyRangeSelection = () => {
    if (!startRoll || !endRoll) {
      alert('Please select both Start and End Roll Numbers.');
      return;
    }

    const start = parseInt(startRoll, 10);
    const end = parseInt(endRoll, 10);

    if (start > end) {
      alert('Start Roll Number must be less than or equal to End Roll Number.');
      return;
    }

    // Select all students falling in range
    const rollNumbersInRange = students
      .filter((s) => s.rollNo >= start && s.rollNo <= end)
      .map((s) => s.rollNo);

    // Merge range selection with existing selected roll numbers without duplicates
    setSelectedStudentRolls((prev) => Array.from(new Set([...prev, ...rollNumbersInRange])));
  };

  const handleSaveGroup = (e) => {
    e.preventDefault();
    if (!groupName.trim()) {
      alert('Please enter a group name.');
      return;
    }
    if (selectedStudentRolls.length === 0) {
      alert('Please select at least one student for the group.');
      return;
    }

    const newGroup = {
      id: Date.now(),
      name: groupName,
      studentRolls: selectedStudentRolls,
    };

    setGroups((prev) => [...prev, newGroup]);
    setGroupNotice(`Group "${groupName}" created with ${selectedStudentRolls.length} student(s).`);

    // AUTO-RESET FORM AND CHECKBOXES
    setGroupName('');
    setSelectedStudentRolls([]); // All checkboxes set to unchecked
    setStartRoll('');
    setEndRoll('');

    setTimeout(() => setGroupNotice(''), 4000);
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 flex flex-col">
      {/* HEADER NAVBAR */}
      <header className="bg-indigo-700 text-white shadow-md">
        <div className="max-w-7xl mx-auto px-4 py-4 flex flex-wrap items-center justify-between">
          <div className="flex items-center space-x-3">
            <SlidersHorizontal className="w-6 h-6" />
            <h1 className="text-xl font-bold tracking-wide">Quiz & Classroom Portal</h1>
          </div>
          <nav className="flex space-x-2 mt-2 sm:mt-0">
            <button
              onClick={() => setActiveTab('question-bank')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition ${
                activeTab === 'question-bank'
                  ? 'bg-white text-indigo-700 shadow-sm'
                  : 'text-indigo-100 hover:bg-indigo-600'
              }`}
            >
              <HelpCircle className="w-4 h-4" />
              <span>Question Bank</span>
            </button>
            <button
              onClick={() => setActiveTab('roster-db')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition ${
                activeTab === 'roster-db'
                  ? 'bg-white text-indigo-700 shadow-sm'
                  : 'text-indigo-100 hover:bg-indigo-600'
              }`}
            >
              <Users className="w-4 h-4" />
              <span>Group Roster DB</span>
            </button>
          </nav>
        </div>
      </header>

      {/* MAIN CONTENT AREA */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6">
        {quizNotice && (
          <div className="mb-4 p-3 bg-emerald-100 border border-emerald-300 text-emerald-800 rounded-md flex items-center space-x-2 animate-fade">
            <CheckCircle className="w-5 h-5 text-emerald-600" />
            <span>{quizNotice}</span>
          </div>
        )}

        {groupNotice && (
          <div className="mb-4 p-3 bg-emerald-100 border border-emerald-300 text-emerald-800 rounded-md flex items-center space-x-2 animate-fade">
            <CheckCircle className="w-5 h-5 text-emerald-600" />
            <span>{groupNotice}</span>
          </div>
        )}

        {/* ========================================================================= */}
        {/* TAB 1: QUESTION BANK DATABASE */}
        {/* ========================================================================= */}
        {activeTab === 'question-bank' && (
          <section className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="p-5 border-b border-slate-200 flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-50">
              <div>
                <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2">
                  <ListFilter className="w-5 h-5 text-indigo-600" />
                  Topic-Wise Question Bank Database
                </h2>
                <p className="text-xs text-slate-500">
                  Filter questions and select them for live quizzes or bulk deletion.
                </p>
              </div>

              {/* FILTERS */}
              <div className="flex flex-wrap items-center gap-3">
                <div className="flex items-center space-x-1">
                  <label className="text-xs font-semibold text-slate-600">Topic:</label>
                  <select
                    value={selectedTopics}
                    onChange={(e) => setSelectedTopics(e.target.value)}
                    className="text-xs border border-slate-300 rounded-md p-2 bg-white focus:ring-2 focus:ring-indigo-500 outline-none"
                  >
                    <option value="All">All Topics</option>
                    <option value="Algorithms">Algorithms</option>
                    <option value="Data Structures">Data Structures</option>
                    <option value="Operating Systems">Operating Systems</option>
                    <option value="Databases">Databases</option>
                  </select>
                </div>

                <div className="flex items-center space-x-1">
                  <label className="text-xs font-semibold text-slate-600">Difficulty:</label>
                  <select
                    value={selectedDifficulty}
                    onChange={(e) => setSelectedDifficulty(e.target.value)}
                    className="text-xs border border-slate-300 rounded-md p-2 bg-white focus:ring-2 focus:ring-indigo-500 outline-none"
                  >
                    <option value="All">All Difficulties</option>
                    <option value="Easy">Easy</option>
                    <option value="Medium">Medium</option>
                    <option value="Hard">Hard</option>
                  </select>
                </div>
              </div>
            </div>

            {/* QUESTIONS TABLE */}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-600">
                <thead className="bg-slate-100 text-slate-700 text-xs uppercase font-semibold border-b border-slate-200">
                  <tr>
                    <th className="p-3 w-10 text-center">
                      <input
                        type="checkbox"
                        checked={
                          filteredQuestions.length > 0 &&
                          selectedQuestionIds.length === filteredQuestions.length
                        }
                        onChange={toggleSelectAllQuestions}
                        className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                      />
                    </th>
                    <th className="p-3 w-20">QID</th>
                    <th className="p-3">Question Text</th>
                    <th className="p-3 w-36">Topic</th>
                    <th className="p-3 w-28">Difficulty</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {filteredQuestions.length === 0 ? (
                    <tr>
                      <td colSpan="5" className="p-6 text-center text-slate-400">
                        No questions match the selected criteria.
                      </td>
                    </tr>
                  ) : (
                    filteredQuestions.map((q) => {
                      const isSelected = selectedQuestionIds.includes(q.id);
                      return (
                        <tr
                          key={q.id}
                          className={`hover:bg-slate-50 transition ${
                            isSelected ? 'bg-indigo-50/50' : ''
                          }`}
                        >
                          <td className="p-3 text-center">
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={() => toggleQuestionSelect(q.id)}
                              className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                            />
                          </td>
                          <td className="p-3 font-mono text-xs font-bold text-slate-500">
                            {q.id}
                          </td>
                          <td className="p-3 font-medium text-slate-800">{q.question}</td>
                          <td className="p-3">
                            <span className="inline-block bg-slate-100 border border-slate-200 rounded-full px-2.5 py-0.5 text-xs text-slate-600 font-medium">
                              {q.topic}
                            </span>
                          </td>
                          <td className="p-3">
                            <span
                              className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-bold ${
                                q.difficulty === 'Easy'
                                  ? 'bg-emerald-100 text-emerald-800'
                                  : q.difficulty === 'Medium'
                                  ? 'bg-amber-100 text-amber-800'
                                  : 'bg-rose-100 text-rose-800'
                              }`}
                            >
                              {q.difficulty}
                            </span>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>

            {/* ACTION PANEL BELOW TABLE */}
            <div className="p-4 bg-slate-50 border-t border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="text-xs text-slate-500">
                Selected: <strong className="text-indigo-600">{selectedQuestionIds.length}</strong> / {filteredQuestions.length} questions
              </div>

              {/* ACTION BUTTONS */}
              <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto">
                <button
                  onClick={handleDeleteSelectedQuestions}
                  disabled={selectedQuestionIds.length === 0}
                  className={`flex-1 sm:flex-none flex items-center justify-center space-x-2 px-4 py-2 rounded-lg text-sm font-semibold transition ${
                    selectedQuestionIds.length > 0
                      ? 'bg-rose-600 hover:bg-rose-700 text-white shadow-sm'
                      : 'bg-slate-200 text-slate-400 cursor-not-allowed'
                  }`}
                >
                  <Trash2 className="w-4 h-4" />
                  <span>Delete Selected ({selectedQuestionIds.length})</span>
                </button>

                <button
                  onClick={handleCreateLiveQuiz}
                  disabled={selectedQuestionIds.length === 0}
                  className={`flex-1 sm:flex-none flex items-center justify-center space-x-2 px-4 py-2 rounded-lg text-sm font-semibold transition ${
                    selectedQuestionIds.length > 0
                      ? 'bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm'
                      : 'bg-slate-200 text-slate-400 cursor-not-allowed'
                  }`}
                >
                  <PlusCircle className="w-4 h-4" />
                  <span>Create Live Quiz ({selectedQuestionIds.length})</span>
                </button>
              </div>
            </div>
          </section>
        )}

        {/* ========================================================================= */}
        {/* TAB 2: CLASSROOM & GROUP ROSTER DATABASE */}
        {/* ========================================================================= */}
        {activeTab === 'roster-db' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* GROUP CREATION FORM & ROSTER */}
            <section className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-slate-200 p-5 flex flex-col justify-between">
              <div>
                <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2 mb-1">
                  <Users className="w-5 h-5 text-indigo-600" />
                  Create Student Group
                </h2>
                <p className="text-xs text-slate-500 mb-5">
                  Set a group name, use roll number ranges or manual selection, then save. Checkboxes reset automatically after creation.
                </p>

                <form onSubmit={handleSaveGroup} className="space-y-5">
                  {/* GROUP NAME INPUT */}
                  <div>
                    <label className="block text-xs font-bold uppercase text-slate-600 mb-1">
                      Group Name
                    </label>
                    <input
                      type="text"
                      value={groupName}
                      onChange={(e) => setGroupName(e.target.value)}
                      placeholder="e.g. Group A - Advanced Physics"
                      className="w-full border border-slate-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                    />
                  </div>

                  {/* RANGE SELECTION DROPDOWNS */}
                  <div className="bg-indigo-50/60 border border-indigo-100 rounded-lg p-4">
                    <label className="block text-xs font-bold text-indigo-900 uppercase mb-2">
                      Quick Select by Roll Number Range
                    </label>
                    <div className="flex flex-wrap items-center gap-3">
                      <div className="flex items-center space-x-2">
                        <span className="text-xs text-slate-600 font-medium">From Roll No:</span>
                        <select
                          value={startRoll}
                          onChange={(e) => setStartRoll(e.target.value)}
                          className="text-xs border border-slate-300 rounded-md p-2 bg-white focus:ring-2 focus:ring-indigo-500 outline-none"
                        >
                          <option value="">Select</option>
                          {students.map((s) => (
                            <option key={`start-${s.rollNo}`} value={s.rollNo}>
                              {s.rollNo} ({s.name})
                            </option>
                          ))}
                        </select>
                      </div>

                      <div className="flex items-center space-x-2">
                        <span className="text-xs text-slate-600 font-medium">To Roll No:</span>
                        <select
                          value={endRoll}
                          onChange={(e) => setEndRoll(e.target.value)}
                          className="text-xs border border-slate-300 rounded-md p-2 bg-white focus:ring-2 focus:ring-indigo-500 outline-none"
                        >
                          <option value="">Select</option>
                          {students.map((s) => (
                            <option key={`end-${s.rollNo}`} value={s.rollNo}>
                              {s.rollNo} ({s.name})
                            </option>
                          ))}
                        </select>
                      </div>

                      <button
                        type="button"
                        onClick={handleApplyRangeSelection}
                        className="px-3 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md text-xs font-semibold transition"
                      >
                        Apply Range Selection
                      </button>
                    </div>
                  </div>

                  {/* ROSTER LIST WITH CHECKBOXES */}
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <label className="text-xs font-bold uppercase text-slate-600">
                        Student Roster List
                      </label>
                      <button
                        type="button"
                        onClick={() => setSelectedStudentRolls([])}
                        className="text-xs text-indigo-600 hover:underline flex items-center space-x-1"
                      >
                        <RefreshCw className="w-3 h-3" />
                        <span>Clear All Checkboxes</span>
                      </button>
                    </div>

                    <div className="max-h-60 overflow-y-auto border border-slate-200 rounded-lg divide-y divide-slate-100 bg-slate-50 p-1">
                      {students.map((student) => {
                        const isChecked = selectedStudentRolls.includes(student.rollNo);
                        return (
                          <label
                            key={student.rollNo}
                            className={`flex items-center justify-between p-2 rounded cursor-pointer transition text-xs ${
                              isChecked ? 'bg-indigo-100/70 font-semibold text-indigo-900' : 'hover:bg-slate-100 text-slate-700'
                            }`}
                          >
                            <div className="flex items-center space-x-3">
                              <input
                                type="checkbox"
                                checked={isChecked}
                                onChange={() => toggleStudentSelect(student.rollNo)}
                                className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                              />
                              <span className="font-mono bg-white px-2 py-0.5 border border-slate-200 rounded font-bold text-slate-600">
                                {student.rollNo}
                              </span>
                              <span>{student.name}</span>
                            </div>
                            <span className="text-slate-400 text-[10px]">
                              {isChecked ? 'Selected' : 'Unselected'}
                            </span>
                          </label>
                        );
                      })}
                    </div>
                  </div>

                  {/* SUBMIT BUTTON */}
                  <div className="pt-2 flex justify-between items-center">
                    <span className="text-xs text-slate-500">
                      Total Selected: <strong className="text-indigo-600">{selectedStudentRolls.length}</strong> students
                    </span>
                    <button
                      type="submit"
                      className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-bold shadow-sm transition"
                    >
                      Save Group
                    </button>
                  </div>
                </form>
              </div>
            </section>

            {/* CREATED GROUPS DISPLAY */}
            <section className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
              <h3 className="text-md font-bold text-slate-800 mb-3 border-b border-slate-100 pb-2">
                Created Groups ({groups.length})
              </h3>
              {groups.length === 0 ? (
                <p className="text-xs text-slate-400 italic py-6 text-center">
                  No groups created yet. Create a group on the left panel.
                </p>
              ) : (
                <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
                  {groups.map((group) => (
                    <div
                      key={group.id}
                      className="border border-slate-200 rounded-lg p-3 bg-slate-50 hover:border-indigo-200 transition"
                    >
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="font-bold text-sm text-indigo-900">{group.name}</h4>
                        <span className="bg-indigo-100 text-indigo-800 text-[10px] font-bold px-2 py-0.5 rounded-full">
                          {group.studentRolls.length} Students
                        </span>
                      </div>
                      <div className="text-xs text-slate-600">
                        <p className="font-semibold text-slate-500 mb-1">Assigned Roll Numbers:</p>
                        <div className="flex flex-wrap gap-1">
                          {group.studentRolls.map((roll) => (
                            <span
                              key={roll}
                              className="bg-white border border-slate-200 px-1.5 py-0.5 rounded text-[11px] font-mono text-slate-700"
                            >
                              {roll}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </div>
        )}
      </main>
    </div>
  );
}
