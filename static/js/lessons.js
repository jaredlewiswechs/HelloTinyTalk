/**
 * TinyTalk Lesson Engine
 * Provides interactive lessons in the Learn tab.
 * Loaded before rstudio.js — exposes window.LessonEngine.
 */

/* global window, fetch, localStorage, document */

window.LessonEngine = (function () {
  'use strict';

  var lessons = [];
  var currentLesson = 0;
  var currentStep = 0;
  var progress = {}; // { lessonId: numberOfCompletedSteps }

  var STORAGE_KEY = 'tinytalk_lesson_progress';

  function loadProgress() {
    try {
      progress = JSON.parse(localStorage.getItem(STORAGE_KEY)) || {};
    } catch (e) {
      progress = {};
    }
  }

  function saveProgress() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(progress));
  }

  function isLessonComplete(lesson) {
    var exerciseCount = lesson.steps.filter(function (s) { return s.type === 'exercise'; }).length;
    return (progress[lesson.id] || 0) >= exerciseCount;
  }

  function getCompletedExercises(lesson) {
    return progress[lesson.id] || 0;
  }

  function getExerciseCount(lesson) {
    return lesson.steps.filter(function (s) { return s.type === 'exercise'; }).length;
  }

  function escapeHtml(str) {
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function formatContent(text) {
    // Convert `code` to <code> tags
    return escapeHtml(text).replace(/`([^`]+)`/g, '<code>$1</code>');
  }

  // ── Render ──────────────────────────────────────────────────────

  function render() {
    var container = document.getElementById('learn-container');
    if (!container || lessons.length === 0) return;

    var lesson = lessons[currentLesson];
    var step = lesson.steps[currentStep];

    var html = '';

    // Sidebar
    html += '<div class="lesson-sidebar">';
    html += '<div class="lesson-sidebar-title">Lessons</div>';
    lessons.forEach(function (l, i) {
      var completed = isLessonComplete(l);
      var active = i === currentLesson;
      html += '<div class="lesson-item' + (active ? ' active' : '') + (completed ? ' completed' : '') + '" data-lesson="' + i + '">';
      html += '<span class="lesson-check">' + (completed ? '&#10003;' : '&#9675;') + '</span>';
      html += '<span>' + escapeHtml(l.title) + '</span>';
      html += '</div>';
    });
    html += '</div>';

    // Content
    html += '<div class="lesson-content">';

    // Progress bar
    var exercisesDone = getCompletedExercises(lesson);
    var exercisesTotal = getExerciseCount(lesson);
    var pct = exercisesTotal > 0 ? (exercisesDone / exercisesTotal * 100) : 0;
    html += '<div class="lesson-progress-bar"><div class="lesson-progress-fill" style="width:' + pct + '%"></div></div>';

    // Step content
    html += '<div class="lesson-step-title">' + escapeHtml(step.title) + '</div>';
    html += '<div class="lesson-step-text">' + formatContent(step.content) + '</div>';

    if (step.code) {
      html += '<div class="lesson-code-block">' + escapeHtml(step.code) + '</div>';
    }

    if (step.type === 'explain') {
      html += '<div class="lesson-actions">';
      if (step.code) {
        html += '<button class="lesson-btn lesson-btn-primary" id="lesson-run-example">Run Example</button>';
      }
      html += '</div>';
    }

    if (step.type === 'exercise') {
      html += '<div class="lesson-actions">';
      html += '<button class="lesson-btn lesson-btn-success" id="lesson-check">Check Answer</button>';
      if (step.starterCode) {
        html += '<button class="lesson-btn lesson-btn-primary" id="lesson-load-starter">Load Starter Code</button>';
      }
      if (step.hint) {
        html += '<button class="lesson-btn lesson-btn-secondary" id="lesson-show-hint">Show Hint</button>';
      }
      html += '</div>';

      if (step.hint) {
        html += '<div class="lesson-hint" id="lesson-hint">' + formatContent(step.hint) + '</div>';
      }

      html += '<div id="lesson-result"></div>';
    }

    // Navigation
    html += '<div class="lesson-nav">';
    if (currentStep > 0 || currentLesson > 0) {
      html += '<button class="lesson-btn lesson-btn-secondary" id="lesson-prev">&larr; Previous</button>';
    } else {
      html += '<span></span>';
    }
    if (currentStep < lesson.steps.length - 1 || currentLesson < lessons.length - 1) {
      html += '<button class="lesson-btn lesson-btn-primary" id="lesson-next">Next &rarr;</button>';
    } else {
      html += '<span></span>';
    }
    html += '</div>';

    html += '</div>'; // .lesson-content

    container.innerHTML = html;
    bindEvents();
  }

  // ── Events ──────────────────────────────────────────────────────

  function bindEvents() {
    // Sidebar clicks
    document.querySelectorAll('.lesson-item').forEach(function (item) {
      item.addEventListener('click', function () {
        currentLesson = parseInt(item.dataset.lesson, 10);
        currentStep = 0;
        render();
      });
    });

    // Run example
    var runBtn = document.getElementById('lesson-run-example');
    if (runBtn) {
      runBtn.addEventListener('click', function () {
        var step = lessons[currentLesson].steps[currentStep];
        if (window._ttEditor && step.code) {
          window._ttEditor.setValue(step.code);
          // Trigger run via the source run button
          document.getElementById('btn-run').click();
        }
      });
    }

    // Load starter code
    var starterBtn = document.getElementById('lesson-load-starter');
    if (starterBtn) {
      starterBtn.addEventListener('click', function () {
        var step = lessons[currentLesson].steps[currentStep];
        if (window._ttEditor && step.starterCode) {
          window._ttEditor.setValue(step.starterCode);
          window._ttEditor.focus();
        }
      });
    }

    // Show hint
    var hintBtn = document.getElementById('lesson-show-hint');
    if (hintBtn) {
      hintBtn.addEventListener('click', function () {
        var hintEl = document.getElementById('lesson-hint');
        if (hintEl) hintEl.classList.toggle('visible');
      });
    }

    // Check answer
    var checkBtn = document.getElementById('lesson-check');
    if (checkBtn) {
      checkBtn.addEventListener('click', checkAnswer);
    }

    // Navigation
    var prevBtn = document.getElementById('lesson-prev');
    if (prevBtn) {
      prevBtn.addEventListener('click', function () {
        if (currentStep > 0) {
          currentStep--;
        } else if (currentLesson > 0) {
          currentLesson--;
          currentStep = lessons[currentLesson].steps.length - 1;
        }
        render();
      });
    }

    var nextBtn = document.getElementById('lesson-next');
    if (nextBtn) {
      nextBtn.addEventListener('click', function () {
        goNext();
      });
    }
  }

  function goNext() {
    var lesson = lessons[currentLesson];
    if (currentStep < lesson.steps.length - 1) {
      currentStep++;
    } else if (currentLesson < lessons.length - 1) {
      currentLesson++;
      currentStep = 0;
    }
    render();
  }

  // ── Validation ────────────────────────────────────────────────

  function checkAnswer() {
    var step = lessons[currentLesson].steps[currentStep];
    if (!step.validation || !window._ttEditor || !window._ttRunCode) return;

    var code = window._ttEditor.getValue();
    var resultEl = document.getElementById('lesson-result');
    resultEl.innerHTML = '<div class="lesson-result" style="color:var(--text-muted)">Checking...</div>';

    window._ttRunCode(code, function (data) {
      var valid = false;
      var output = (data.output || '').trim();
      var v = step.validation;

      switch (v.mode) {
        case 'output_contains':
          valid = output.toLowerCase().indexOf(v.expect.toLowerCase()) !== -1;
          break;
        case 'output_equals':
          valid = output === v.expect.trim();
          break;
        case 'output_match':
          try { valid = new RegExp(v.expect).test(output); } catch (e) { valid = false; }
          break;
        case 'no_error':
          valid = data.success === true;
          break;
        default:
          valid = data.success === true;
      }

      if (valid) {
        resultEl.innerHTML = '<div class="lesson-result success">Correct! Well done.</div>';
        // Track progress
        var lesson = lessons[currentLesson];
        var exerciseIndex = 0;
        for (var i = 0; i < currentStep; i++) {
          if (lesson.steps[i].type === 'exercise') exerciseIndex++;
        }
        var prev = progress[lesson.id] || 0;
        if (exerciseIndex + 1 > prev) {
          progress[lesson.id] = exerciseIndex + 1;
          saveProgress();
        }
        // Auto-advance after delay
        setTimeout(function () {
          goNext();
        }, 1200);
      } else {
        var msg = 'Not quite.';
        if (v.mode === 'output_contains') {
          msg += ' Your output should contain "' + escapeHtml(v.expect) + '".';
        } else if (!data.success) {
          msg += ' Error: ' + escapeHtml(data.error || 'unknown error');
        } else {
          msg += ' Check the expected output and try again.';
        }
        resultEl.innerHTML = '<div class="lesson-result failure">' + msg + '</div>';
      }
    });
  }

  // ── Init ──────────────────────────────────────────────────────

  function init() {
    loadProgress();
    fetch('/static/data/lessons.json')
      .then(function (r) { return r.json(); })
      .then(function (data) {
        lessons = data.lessons || [];
        if (lessons.length > 0) render();
      })
      .catch(function (err) {
        var container = document.getElementById('learn-container');
        if (container) {
          container.innerHTML = '<div style="padding:24px;color:var(--text-muted);text-align:center;">Could not load lessons.</div>';
        }
      });
  }

  return { init: init };
})();
