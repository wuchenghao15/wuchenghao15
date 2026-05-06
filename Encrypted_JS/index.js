
// 加密JS包装器
(function() {
    const encryptedData = 'ykPoXjtnrsik4o9neUqVkkJ7L9etD0k8Rk2zafHaijNJRgN5YCCOP28t0DTyZUqljQzun4i6GLeLTlbM5fSgZtx77xUdACA+BQup6t+/trBoQH2W808fdyuOzZi5Ltgx+UfN+vCrlZHtXc3j+n1I8r0gyl8zSRL0FnmPd8TvDF7G9GqM8MRFByCEbcP9dOCVvX4Tgixyy5JBnvSEoP11HFg9MSmvq+4iF3qJZKQpmoj1jCe/QI3Qa04IA9dyTKmKKAYJ9ZOvB40MAJ29iA72RR7jf4LsDLIJKd/Xcw/kfF8RLB2KXMyLGtaU23eIQn8zw8f1y5Thms4QQK6j6oWxA9paT7PqR/en39JGXQRNE/AMqEf3Kt0k9QFm+rUQNBsTpyu0++00caKZ8rlnfXN9mT+egApHoOZhLC1zg1Gxvxmh2bfZ82HyqMRrfVmTH/upE0CJXAwj5LRcWdfG1DQ4YOgz4aWZPgRrfc+J0xt0CWnwtGKSnKO5SbdiFx03L9PoQoFkyCP346UXJVobfrOxnJPFW3SSZRSwjxtngPj541NrGPZlMrfDKMLyHfxlf+uDIopQldn4NtAvydThbl9fUVWSmVWfWr6jjuTJOzK5HbFDuBirEsUjAF0SjJuIegL8esVa/uibk9P0Az523ETNUW5+P4+OyMZM5JF4ueoyp1XI452dCd8Qhc4HNGKwdM1UWaI74VmqZFZZlUe3Q91mNV+f4dQtV2q7J+4ikWq/vaRqtRKER43Dl6uOc42j05Ducdqs2lZ/vs34KZ9id4ODVhkbT7nz++MrcNUUyUUdREDo5GAjxz9ILi+WSeBN0YpHYU15xccAmDasc43UJOnv6HqK8ho4bKRtR6AB9vvO6C735Ih9TwAIz42By3e5YXu+f+qXyD8abiCj3h87UCf/g0Adkz0+0ptQD2c3e9WG5iLFsCO+bCtAWVTdFCTTX8zbQKUxBqI70pQB7MBh9MyLqWr/AF0hYfx1kEhQerbsdPtPQNFlzIG/lmTJ46VpYHmYmNNeMzLh/dqRBwDeJPDXj9M7Tj3R3FRlWsJbTwcRxxYcq4Usdb3UikYuyA6Lejpv3dVmUbGwtbhP4GQx++I/dCkrgPDUN+Hyh7h7uZctPij/n28Kj/+WrHR6GUfbI7uJaTzVX7wL9JCwM5AOWo3KLpg9qxI1LfE6Na8LjxDuoXWuT4LKoCbGyaV99FmXKSjWttYmYVzXOfyyJCY4yGuetzbpYbzeuoqv3//UM+YlsAx7biCK14+lGgXmXhxTz0KPQZEHRKww4iwSULDeIy9kEOJ4vBhYJfvoAu9cB31yKtMnUJ2aQJ/kuh0zM391EdJpunMIf2RpBJibrcpf/Y7EfwPVhR6tQG4HgAxyKMJdSiSb+D6qjiycclR71hzqmp906CI+uzNqvR36Gr/Kyw22HYlti9f2mXj5wY5BYYkUwd2bTx7m7kPSR5f6bAt7f+wo/x0GN7KvXGf9FulHHjTWNx5MdSSM+QU6I49StfIMItDOiv/x1dGpJ/U3RqW+QI9IiIbdV1lijVymT6sL6KptdvqZC/9M+QP32+lzdeV7ZeiBdCG91IjvPq0RdOis0P+XvHOTuqvC9CvhXsGQLYI7EKweziTtWEA0bKthYuaEz2A4eqKamWDAVMdt06HyL7u5TnsBD/P5ZCnUjQLHbxkFEUtF76Nnw+eRHsELqH78+0XALMqwJHk6zEI/REc3c3fnuiZ7ltcZx3THO5gJdktbxuXpB6riU6OAMoITNstW2MSrTwgtZUMpZ5Lagwc1DjhkFIzDX5QsvOz6v5EQRvRYvOOVDzfeUzLWYFGSV263ZX2UUNR56wXjn1/zr51ctAesXizmU2bZ130Jd53f2bSgA7PFok5yo5d8KVcFPnRAKyw4psCSZO86KQu6+KqFm38U';
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
