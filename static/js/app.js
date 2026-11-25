document.addEventListener('DOMContentLoaded', () => {
    const editSubjectButtons = document.querySelectorAll('.edit-subject-btn');
    editSubjectButtons.forEach((button) => {
        button.addEventListener('click', () => {
            const form = document.getElementById('subject-form');
            const actionField = document.getElementById('subject-action');
            const hiddenId = document.getElementById('subject_id');
            const heading = document.getElementById('subject-form-heading');
            form.querySelector('#subject_code').value = button.dataset.code;
            form.querySelector('#subject_name').value = button.dataset.name;
            form.querySelector('#subject_department').value = button.dataset.department;
            form.querySelector('#subject_semester').value = button.dataset.semester;
            hiddenId.value = button.dataset.id;
            actionField.value = 'edit';
            heading.textContent = 'Edit Subject';
            form.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
    });

    const cancelSubjectEdit = document.getElementById('cancel-subject-edit');
    if (cancelSubjectEdit) {
        cancelSubjectEdit.addEventListener('click', () => {
            const form = document.getElementById('subject-form');
            form.reset();
            document.getElementById('subject-action').value = 'add';
            document.getElementById('subject_id').value = '';
            document.getElementById('subject-form-heading').textContent = 'Add Subject';
        });
    }

    const editStudentButtons = document.querySelectorAll('.edit-student-btn');
    editStudentButtons.forEach((button) => {
        button.addEventListener('click', () => {
            const form = document.getElementById('student-form');
            const actionField = document.getElementById('student-action');
            const hiddenId = document.getElementById('student_db_id');
            form.querySelector('#student_code').value = button.dataset.studentId;
            form.querySelector('#student_name').value = button.dataset.name;
            form.querySelector('#student_program').value = button.dataset.program;
            form.querySelector('#student_year').value = button.dataset.year;
            form.querySelector('#student_email').value = button.dataset.email;
            hiddenId.value = button.dataset.id;
            actionField.value = 'edit';
            form.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
    });

    const cancelStudentEdit = document.getElementById('cancel-student-edit');
    if (cancelStudentEdit) {
        cancelStudentEdit.addEventListener('click', () => {
            const form = document.getElementById('student-form');
            form.reset();
            document.getElementById('student-action').value = 'add';
            document.getElementById('student_db_id').value = '';
        });
    }

    const flashMessages = document.querySelectorAll('.flash');
    flashMessages.forEach((message) => {
        setTimeout(() => {
            message.style.opacity = '0';
            message.style.transform = 'translateY(-5px)';
            setTimeout(() => message.remove(), 300);
        }, 3500);
    });
});
