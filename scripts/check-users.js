/**
 * Check if there are any existing users in the database
 */

const db = require('./src/database/db');

async function checkUsers() {
    try {
        console.log('Connecting to database...');
        await db.initialize();
        
        console.log('Checking for existing users...');
        const users = await db.query('SELECT * FROM users');
        
        if (users.length > 0) {
            console.log(`Found ${users.length} users:`);
            users.forEach(user => {
                console.log(`- ID: ${user.id}, Username: ${user.username}, Email: ${user.email}, Role: ${user.role}`);
            });
        } else {
            console.log('No users found in database.');
            console.log('Creating a test user...');
            
            // Create a test user
            const bcrypt = require('bcrypt');
            const hashedPassword = await bcrypt.hash('test123', 10);
            
            const result = await db.execute(
                'INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)',
                ['testuser', hashedPassword, 'test@example.com', 'user']
            );
            
            console.log(`Test user created with ID: ${result.lastID}`);
        }
        
        console.log('Database check completed.');
    } catch (error) {
        console.error('Error checking users:', error);
    } finally {
        db.close();
    }
}

checkUsers();