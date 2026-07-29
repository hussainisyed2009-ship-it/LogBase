const addBtn = document.getElementById('open-modal-btn');
const goalItem = document.querySelectorAll('.goal-item');
const closeModalBtn = document.getElementById('close-modal-btn');
const deleteGoalBtn = document.querySelectorAll('.delete-goal-btn');
const createClass = document.getElementById('create-class-btn');



// listener for when user clicks on goal
goalItem.forEach(button => {
    button.addEventListener('click', (event) => {
        // get the goal id so we can fetch goal's data
        const id = event.currentTarget.getAttribute('data-id');
        const createdAt = event.currentTarget.getAttribute('data-created_at');
        const text = event.currentTarget.getAttribute('data-text');
        const targetMins = event.currentTarget.getAttribute('data-target_mins');
        const dueDate = event.currentTarget.getAttribute('data-due_date');
        const for_class = event.currentTarget.getAttribute('data-classId'); // id of class the goal is for
        
        document.getElementById("edit-goal-modal").removeAttribute('hidden');

        document.getElementById("edit-goal-desc").value = text;
        document.getElementById("edit-goal-minutes").value = targetMins;
        document.getElementById("edit-goal-due").value = dueDate;
        document.getElementById("edit-goal-id").value = id;
        document.getElementById("edit-goal-class").value = for_class;

        // Clear list and show loading state
        const progressList = document.getElementById('student-progress-list');
        progressList.innerHTML = '<p style="color: var(--muted); font-size: 13px; font-style: italic; margin: 0; text-align: center; padding: 10px 0;">Loading student progress...</p>';

        // make goal to backend and fetch data for the goal for which students completed it
        fetch(`/admin/track/${id}`, {
            method: 'GET',
        })
        .then(response => {
            if (response.ok) {
                return response.json();
            } else {
                return response.json().then(err => {
                    alert("Error loading goal data: " + err.error);
                }); 
            }
        })
        .then(students => {
            if (!students) return;
            progressList.innerHTML = ''; // Clear loading text

            if (students.length === 0) {
                progressList.innerHTML = '<p style="color: var(--muted); font-size: 13px; font-style: italic; margin: 0; text-align: center; padding: 10px 0;">No students registered.</p>';
                return;
            }

            students.forEach(student => {
                const item = document.createElement('div');
                item.style.display = 'flex';
                item.style.justify = 'space-between';
                item.style.alignItems = 'center';
                item.style.padding = '8px 12px';
                item.style.background = 'rgba(255, 255, 255, 0.015)';
                item.style.border = '1px solid var(--border-color)';
                item.style.borderRadius = '8px';
                item.style.fontSize = '14px';

                // Check if they reached the target
                const isGoalReached = student.complete_mins >= targetMins;
                const badgeColor = isGoalReached ? 'var(--success, #2ec866)' : 'var(--accent)';
                const badgeText = isGoalReached ? '🏆 Done' : '⚡ Reading';

                item.innerHTML = 
                    `<span style="color: #ffffff; font-weight: 500;">${student.name}:&nbsp;</span>` +
                    `<div style="display: flex; align-items: center; gap: 8px;">` +
                        `<span style="color: var(--muted); font-size: 13px;"> ${student.complete_mins} / ${targetMins}m</span>` +
                        `<span style="color: ${badgeColor}; font-weight: 700; font-size: 11px; text-transform: uppercase;">${badgeText}</span>` +
                    `</div>`;

                progressList.appendChild(item);
            });
        })
        .catch(error => {
            console.error("Error getting goal data: ", error);
            progressList.innerHTML = '<p style="color: #ff6b6b; font-size: 13px; text-align: center; padding: 10px 0;">Error loading progress.</p>';
        })


    })
})

createClass.addEventListener('click',() => {
    document.getElementById("class-modal").removeAttribute('hidden');
})

const closeClassModalBtn = document.getElementById('close-class-modal-btn');
if (closeClassModalBtn) {
    closeClassModalBtn.addEventListener('click', () => {
        document.getElementById("class-modal").setAttribute("hidden", "");
    });
}

addBtn.addEventListener('click', () => {
    document.getElementById("goal-modal").removeAttribute('hidden');
})

closeModalBtn.addEventListener('click', () => {
    document.getElementById("goal-modal").setAttribute("hidden", "");
})

deleteGoalBtn.forEach(button => {
    button.addEventListener('click', (event) => {
        // Retrieve the data-id parameter from the clicked button
        const goalId = event.target.getAttribute('data-id');

        fetch(`/admin/goals/delete/${goalId}`, {
            method: 'DELETE',
        })
        .then(response => {
            if (response.ok) {
                window.location.reload();
            } else {
                return response.json().then(err => {
                    alert("Error deleting goals: " + err.error);
                });
            }
        })
        .catch(error => {
            console.error("Erorr deleting goal: ", error);
        })
        event.stopPropagation();
    })
})

const editCloseModalBtn = document.getElementById('edit-close-modal-btn');
if (editCloseModalBtn) {
    editCloseModalBtn.addEventListener('click', () => {
        document.getElementById("edit-goal-modal").setAttribute("hidden", "");
    });
}

// listener for clicking on class card
const classItems = document.querySelectorAll('.class-card-item');
classItems.forEach(card => {
    card.addEventListener('click', (event) => {
        const id = event.currentTarget.getAttribute('data-id');
        const name = event.currentTarget.getAttribute('data-name');
        
        const editModal = document.getElementById("edit-class-modal");
        if (editModal) {
            editModal.removeAttribute('hidden');
            document.getElementById("edit-class-id").value = id;
            document.getElementById("edit-class-name").value = name;
        }
    });
});

const editClassCloseBtn = document.getElementById('edit-class-close-btn');
if (editClassCloseBtn) {
    editClassCloseBtn.addEventListener('click', () => {
        document.getElementById("edit-class-modal").setAttribute("hidden", "");
    });
}

const deleteClassBtn = document.getElementById('delete-class-btn');
if (deleteClassBtn) {
    deleteClassBtn.addEventListener('click', () => {
        const classId = document.getElementById('edit-class-id').value;
        if (confirm("Are you sure you want to delete this class?")) {
            fetch(`/admin/class/delete/${classId}`, {
                method: 'DELETE',
            })
            .then(response => {
                if (response.ok) {
                    window.location.reload();
                } else {
                    return response.json().then(err => alert("Error deleting class: " + (err.error || 'Failed')));
                }
            })
            .catch(err => console.error("Error deleting class:", err));
        }
    });
}


