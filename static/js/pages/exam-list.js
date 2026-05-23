/**
 * Exam List Page JavaScript
 * Handles delete and reopen modal functionality for exam management
 */

let currentExamId = null;

function openDeleteModal(examId, examTitle) {
    currentExamId = examId;
    document.getElementById('examTitle').textContent = examTitle;
    document.getElementById('deletePassword').value = '';
    document.getElementById('passwordError').classList.add('hidden');
    document.getElementById('deleteModal').classList.remove('hidden');
    document.getElementById('deletePassword').focus();
}

function closeDeleteModal() {
    document.getElementById('deleteModal').classList.add('hidden');
    currentExamId = null;
}

function confirmDelete() {
    const password = document.getElementById('deletePassword').value;
    const errorDiv = document.getElementById('passwordError');
    
    if (!password) {
        errorDiv.textContent = 'Password is required';
        errorDiv.classList.remove('hidden');
        return;
    }
    
    // Update form action and submit
    const form = document.getElementById('deleteForm');
    form.action = `/exams/${currentExamId}/delete/`;
    form.submit();
}

// Reopen Modal Functions
let currentReopenExamId = null;
let allStudents = [];
let selectedStudentIds = new Set();

function openReopenModal(examId, examTitle) {
    currentReopenExamId = examId;
    document.getElementById('reopenExamTitle').textContent = examTitle;
    document.getElementById('reopenModal').classList.remove('hidden');
    
    // Reset state
    selectedStudentIds.clear();
    document.getElementById('selectAllStudents').checked = false;
    document.getElementById('studentsList').classList.add('hidden');
    document.getElementById('studentsError').classList.add('hidden');
    document.getElementById('studentsEmpty').classList.add('hidden');
    document.getElementById('studentsLoading').classList.remove('hidden');
    document.getElementById('confirmReopenBtn').disabled = true;
    
    // Fetch students
    fetch(`/exams/${examId}/students/`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('studentsLoading').classList.add('hidden');
            
            if (data.success && data.students.length > 0) {
                allStudents = data.students;
                renderStudentsList();
                document.getElementById('studentsList').classList.remove('hidden');
            } else {
                document.getElementById('studentsEmpty').classList.remove('hidden');
            }
        })
        .catch(error => {
            console.error('Error fetching students:', error);
            document.getElementById('studentsLoading').classList.add('hidden');
            document.getElementById('studentsError').classList.remove('hidden');
        });
}

function closeReopenModal() {
    document.getElementById('reopenModal').classList.add('hidden');
    currentReopenExamId = null;
    allStudents = [];
    selectedStudentIds.clear();
}

function renderStudentsList() {
    const container = document.getElementById('studentsList');
    container.innerHTML = '';
    
    allStudents.forEach(student => {
        const div = document.createElement('div');
        div.className = 'modal-student-item';
        div.innerHTML = `
            <input type="checkbox" 
                   id="student_${student.id}" 
                   value="${student.id}" 
                   onchange="toggleStudent(${student.id})"
                   class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500">
            <label for="student_${student.id}" class="ml-2 flex-1 cursor-pointer">
                <span class="modal-student-name">${student.full_name}</span>
                <span class="modal-student-id">${student.school_id}</span>
                <span class="modal-student-class">(${student.class_name})</span>
            </label>
        `;
        container.appendChild(div);
    });
}

function toggleStudent(studentId) {
    const checkbox = document.getElementById(`student_${studentId}`);
    if (checkbox.checked) {
        selectedStudentIds.add(studentId);
    } else {
        selectedStudentIds.delete(studentId);
        document.getElementById('selectAllStudents').checked = false;
    }
    updateConfirmButton();
}

function toggleSelectAll() {
    const selectAll = document.getElementById('selectAllStudents');
    const isChecked = selectAll.checked;
    
    allStudents.forEach(student => {
        const checkbox = document.getElementById(`student_${student.id}`);
        checkbox.checked = isChecked;
        
        if (isChecked) {
            selectedStudentIds.add(student.id);
        } else {
            selectedStudentIds.delete(student.id);
        }
    });
    
    updateConfirmButton();
}

function updateConfirmButton() {
    const btn = document.getElementById('confirmReopenBtn');
    btn.disabled = selectedStudentIds.size === 0;
}

function confirmReopen() {
    if (selectedStudentIds.size === 0) {
        return;
    }
    
    // Create form and submit
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = `/exams/${currentReopenExamId}/activate/`;
    
    // Add CSRF token - try multiple methods
    let csrfToken = null;
    const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
    if (csrfInput) {
        csrfToken = csrfInput.value;
    } else {
        // Try meta tag
        const metaTag = document.querySelector('meta[name=csrf-token]');
        if (metaTag) {
            csrfToken = metaTag.getAttribute('content');
        } else {
            // Try cookie
            const cookies = document.cookie.split(';');
            for (let cookie of cookies) {
                const [name, value] = cookie.trim().split('=');
                if (name === 'csrftoken') {
                    csrfToken = value;
                    break;
                }
            }
        }
    }
    
    if (!csrfToken) {
        return;
    }
    
    const csrfInputField = document.createElement('input');
    csrfInputField.type = 'hidden';
    csrfInputField.name = 'csrfmiddlewaretoken';
    csrfInputField.value = csrfToken;
    form.appendChild(csrfInputField);
    
    // Add selected student IDs
    selectedStudentIds.forEach(studentId => {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'student_ids';
        input.value = studentId;
        form.appendChild(input);
    });
    
    // Add select_all flag if all students are selected
    if (document.getElementById('selectAllStudents').checked) {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'select_all';
        input.value = '1';
        form.appendChild(input);
    }
    
    document.body.appendChild(form);
    form.submit();
}

// Initialize event listeners when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Close delete modal when clicking outside
    const deleteModal = document.getElementById('deleteModal');
    if (deleteModal) {
        deleteModal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeDeleteModal();
            }
        });
    }

    // Handle Enter key in delete password field
    const deletePassword = document.getElementById('deletePassword');
    if (deletePassword) {
        deletePassword.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                confirmDelete();
            }
        });
    }

    // Close reopen modal when clicking outside
    const reopenModal = document.getElementById('reopenModal');
    if (reopenModal) {
        reopenModal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeReopenModal();
            }
        });
    }
});