const path = require('path');
const sqlite3 = require('sqlite3').verbose();
const bcrypt = require('bcrypt');

// 連接資料庫
const dataDir = path.join(__dirname, '..', 'data');
const dbPath = path.join(dataDir, 'app.db');
const db = new sqlite3.Database(dbPath);

// 新增使用者函數
function addUser(name, studentId, username, password) {
  return new Promise((resolve, reject) => {
    // 檢查使用者名稱是否已存在
    db.get("SELECT id FROM users WHERE username = ?", [username], (err, row) => {
      if (err) {
        reject(err);
        return;
      }
      
      if (row) {
        reject(new Error(`使用者名稱 '${username}' 已存在`));
        return;
      }
      
      // 加密密碼
      const hashedPassword = bcrypt.hashSync(password, 10);
      
      // 新增使用者
      db.run(
        "INSERT INTO users (name, student_id, username, password_hash, role) VALUES (?, ?, ?, ?, ?)",
        [name, studentId, username, hashedPassword, 'admin'],
        function(err) {
          if (err) {
            reject(err);
          } else {
            resolve({
              id: this.lastID,
              name,
              studentId,
              username
            });
          }
        }
      );
    });
  });
}

// 新增指定的使用者
async function main() {
  try {
    console.log('開始新增使用者...');
    
    const newUser = await addUser(
      'scuds13173149', // name
      'scuds13173149', // student_id
      'scuds13173149', // username
      '5028'           // password
    );
    
    console.log('✅ 使用者新增成功:');
    console.log(`   ID: ${newUser.id}`);
    console.log(`   姓名: ${newUser.name}`);
    console.log(`   學號: ${newUser.studentId}`);
    console.log(`   帳號: ${newUser.username}`);
    console.log(`   角色: admin`);
    
  } catch (error) {
    console.error('❌ 新增使用者失敗:', error.message);
  } finally {
    db.close((err) => {
      if (err) console.error('關閉資料庫錯誤:', err);
      else console.log('資料庫連線已關閉');
    });
  }
}

// 執行
main();