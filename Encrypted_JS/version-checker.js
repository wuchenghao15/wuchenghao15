
// 加密JS包装器
(function() {
    const encryptedData = '2dBrsVRVW5eN+ukoYSH6B14xJoGaOZlziiSoMegqHSTvXI58rTQarbidB3GfUVtYJz6ra8WzW1+VQ/FBuBcFh6p5Y9kzTqgP/T6FRj8UlxOmhQerA7CwMy82sRgIJyJ7OeX+7RJ9Rky850Nah1uZfMyTI56zBaEJpK3Cbdgbc57xRWuctZiiPEjiUA+rK9e8bKrOlRI2p545VHBfnVxX9hC9W4SGj3TMZv9qO6fJ0xCfcCRFT2u4m9YCAIykQx+rG2uFbxmTYboByBdaZ/kOK5HW6hp9PnfIYv6WCurbIeaKPKYTs32D41sWOBqKbhIcWq4A2SW2Vj8EybywlOCpgPYtnyrtQjV8umaOdjYIY3ic3sK6y0+uIuwMqXF694OMP5NwuRJQ/0NXS+um/QOz2XU/E6SiZt7p5sxrDixPe5FhSYtO0dbVWlIIxIZtARBDrgG26AAMaI96o5XrHU6kc/fwFnrpfa1oOVyB9wjHrX8v1hAEjHJ575WYMKUjJIiFTIvHv4TCJ2NMLr6xqpuqaAUsldfwOTdtf4E7gISYWSdhT5jPc3tSjywxCueFQiK+tw7eEAieE67iG6HpgGTaHglS5c+rnlfbuCkrj6fZoGqm1QFr7qnRLoX6y6igcAaYnsyG77p+4QEfMEErevHH1GMqg+sYLzEm1N9gZAHjSGEOCR+GySlzMVLspbUB90Q21jMa0yaEjjVimQxH3m+qRaAwaeiBnX0Vz9RlIaCCPZNeKdq7GIbS7GdIsN9tRMLz34ODd4MX4hnoiK+oMxRCqE/P5ZGj0jazdXtGNGPx4zKXzbOKV3fkbgTx5eASwQpzxWXQdXgxownx2wXWaiu5YgnlvbTUhDBEzD1+noOaRDKbn9d+z9Ju7+D1wmrlxZaVtVcJ7YRIf458EgAXKjqIa5dmzdoOASTtv7Zt7yLvtQoHxvuGkV2inBXqmKTLRwxg6hbEyRJm7aXEFdgXf99v5VbAapMj4VhXkN1CWEZ2IYpfjpyX7FB3G0phiZltaCNkKbIO4DFYBM4rY7YgMoCom3c4dtHRbd21pvZcIM+8DAefQsrmy7+r3k8wMnd1V+hPX1HPMDNjGL5ouCeNnV4tSvzsnd3RwTaNLReZ/S1thGI77MFzXo0jeinmHLuHjb581V+qKlg4tTzgZP60TuJA5g==';
    const iv = 'dBYEc2ZuoXPtUV4L3NCuvQ==';
    
    // 解密函数
    function decrypt(data, iv) {
        try {
            // 实际应用中，解密函数应该更安全，这里仅作为演示
            const key = CryptoJS.SHA256('MTSCOS_SECRET_KEY_2025').toString().substring(0, 32);
            const decrypted = CryptoJS.AES.decrypt(
                { ciphertext: CryptoJS.enc.Base64.parse(data) },
                CryptoJS.enc.Utf8.parse(key),
                { iv: CryptoJS.enc.Base64.parse(iv) }
            );
            return decrypted.toString(CryptoJS.enc.Utf8);
        } catch (e) {
            console.error('解密失败:', e);
            return '';
        }
    }
    
    // 解密并执行代码
    try {
        const decryptedCode = decrypt(encryptedData, iv);
        if (decryptedCode) {
            // 使用Function构造器执行代码，避免直接eval
            (new Function(decryptedCode))();
        }
    } catch (e) {
        console.error('执行解密代码失败:', e);
    }
})();
