
// 加密JS包装器
(function() {
    const encryptedData = 'O/N/OUp1lx4Xd2eTdSDIaNgyHkI+HTr9evx2x9/IRZRe+1kR22wm9c4d2RRmT3JYlH/5KwAdXD1+W4BngL+vaC7kFNRjwuSmI3ulIhHOOy/MOwNpf/ozAZQKIxnJQ3sasCbpfKauAb0tQE8QUlkkL0EuBJycRocMBEDlEe/rdKx89cdFvAKpgeTytzMMqR9rH5q9QMH8fTmXTKkclCuvtzNJSLmPm8Q1aSaedJqtY/1DIfMn9LcBinsUVtvIi6mjmH28Ko9n+oG1q3t1qAVWxPfeZfoUJxGeLBvdazdg0fZ+29nTagdKDGiwYY0/UbJvR0tRym20YxV4UGBEh14jSyMPCCk29zaNW4TPXV4znOAWg4l3cNZHmHhbFlxTa1qgJRa5mOvKBCwZet7ODBykfk2X8NbEn4a8eHojM3sHdS2hFl+4dZ8cl9KETnHbmepiblEBsuI9r7CnVRvi35FKRLy/x6TprA2y1/yk4WaTfF6PvckPzgJYcoIX5/hS/LLyY+IDrZ+D8g0Wcv23PS+cRLSdeqiB5E9vKiOZ1lgRKQ5nvKtdDRS7lK7CSjYBZfxwWPrg7sg5RhgaunwAQUetc/U0Xa44S1KaNChUuYIyaEULY9NUo/tmI6E1NHmxIvqmMc3lbbyKwheZ26f4wJbmkk+s9aSMEeORZkslwp8D02B+BbLgP7/dCQRG16oQDd7XWYxWRQh62PSSNA5M5wnI+gAaAF0/v1LkFIPISecpVbPqfNvEasr8YMMXhnpjxrD1sd1wlRlHdDj/MgFx8FCceEwdjyeEa6zY5I6xFHd6/37VgPu09J5D1sRaUXCfEa1SwOwUs2vvnIztv6GWEPD9+gcAlBjojDc8+oy41rKKBKXWMi+eKVIoXO+OOX2AjIE5LmVB2Ptw8N4Vp/jQLH/7KD9ft1AwHQGAL773TyjH3UseW/qQMeJDwv5A5MIT2naKGQ9nCJtvz2CCb7nvmRXYpoeyZD5JJdWsjPpwP9F2LWRqSuCvZewtAyv33WG6xsWNLpPPdzegPq06J3g+IHhuit55hj/pOSD84tSVd3OhJZI8fpFPboZGg5UmO8Dfw3TM/kVDqWw5QJ9r+MgPVxWVY4/OibMwIC4eAl5VEUUTwGHNxCLspdivGcSR1vLm0dTfph4lUaFpdZu6C1XOkPvNMytm20R8ToMDskrIKeT9MQ2nRAqCpdCnqJgSjET3qq5e3KNkHQXnVno07pPmM3bR6EyWeL9d1vCSo6E+vJRLKDLCOC+kzv7C2wmWjfsBBe/LytL1Fvb+o2rkGHAnXuM2WG3FvAF8ph23zlgnXNPQi7EFsFyVDZwewI06dZKCieltAlgZHpjjVOE6TJIOGEmjaxEE/H7vnTtHpmR/ArvxYBo7AlvuqqXQHRwBKtBWi/zBXxX6vSHr1MVz7WTODVp1U6epPuOtCJn5V/vJDndQfXPFkIJzVnuYSwqC8GViO/NKy4U5tr9TvtMUuk0Tf+3rAdRXOoVkmDulFTuIphVJlsvhCxdRaH6cE8JUa4mSTZxxtIt4U1UX/AC5Bp/cGjxFrv1l0qY2/F3vxYxEiusQq3UVrmGn2Q39+Hb6Zg3WL2TQnB42UgBH0r+Z57yxko4bymTdaYAER3DfG8dXJ6E0H3Npmg0ykwRSP4LdOIa/if1oTTRp7EYY9viZxGVd6G3XcVur60xxaC2Q6/lfvRdpDl5uXrNgl5tNP7DAxHHvm2qsbfZamMxo+Ceb0+xp6l6ePECN4WK4h2Tp95ondIE/I+HGLAqPRhhrbDPVF+NXoAvpMQtYyXBv9ZmhEqnKPo/QUEabzmaLwvCTC4DrjgUHAmoOLEJl4uq4Cn1likLupjRuRuGL4E/+5d8znkcgpAkhfAUj4whJPoXTDmsN1ZkVRkf4MoadmRZHjGRmPrQL711gy+qaKQx3hhhqiAl93GEbadtLU6LQC9aLW479TmX8tPAhLg9DxZAYnOAgDOmOChXbgIt6yRLLsxo6KECBApEwVI8NIQd3NL0aX/XTMQSH3j5XqLUXp7+eukZOBQyyzxX9Ubxt+Zi/I8K0uRCWbs+Z0aJk1QzTwUZAjnDs6CJZp7ir8ngqtUzls65h2iQCbhFWWkf/+ztsPyViMlczxF7s1r7GmiKVOVYWclolIxGSX8qVbwthLncE86UqC+eQMa91hZpOIOhUXwLHRH/YOs78QOSDI0UCdWPG2KYGF4JCu+aWe8Sw59WQqpno5a/TGu1Qqg9MNuuB66pczrpSb8zCA5Nc7LeAUvCCY+Nb90THUX0GtxgLCCSPGhnIst1I2Ran7IaOci/gz7BrQcBSP42iAGjSC0DMV6UCZDjBOgWo/MRC78x+5tgkAYenL/eft9KUtTOrN/eDAPI6w0dXNLnVKM6xKr9He1lBfAWVr/cqOyJFHc9Vf2uLztAroBSPp3cypbXLRMSV8Za/ppmXdztgemO2v6FfjIgTR7ck9OVAayLZhWx0/IELlRWOmZuIKUL2oj+f1wPcameEnplNukecvDsqglR95YFo7T6QJhjgzhmvdgpjUPTAnuJ6Sd5TrKytA/wTT9Iqb3/3JM6TsgKpv6TC762Nnhy76vUE5E/9im7jmybFujvZrxlZS+um+NLOAigCoa/nrET3fMmyJRN/p5ioMKIloP+Kk1rxBcuPR8A5Htloyg/i2Ys/fcBdUmUAAmMDLdogZlEgCY3Zw7ekT3Qu1KjtPPuqmvSrS5jVHd/DGMtSn6Qycy7miOAD/ux8QKmLk0mRHLAW2qmG8iWaDJiS6ex0IVprOveXmJ0yAtr9QEO9aYJQ/hGVooaMUfQRGswwI+3+FaRbzdEBincOQcuPaIJ/mf2uKYrng2SyrB2MjE19MsCkwqiL+ErioOLBcm+WAymvG0aUFmp4w2EaJyjEHewamtDXBnaQjU9zEuJKDkRqryNQunPNeuzr/LgZlHA0cYwjA46uZDV3dbdb70xC++X4GbDa03fsnmbFA8y9Ye8TqHQs+EHxc+NhxehiOs8VtMO9gV6TWoGuQODouT88uC66l7g0RVNWKZHl2xmdPE090rF5cXsteWcNAbnk9Km7wyThCmxhTuFAMOYSKof+ZO3yDYho9xZg5mj9Vum1uj/tkrltuz2Z23LFKZwAjPEhHR/VrHbqxbLZ9WXI67GivOeFWsTYBc/WxrGNJKzgJLxKk6+TYDimoj2stIVNN2CLI+6ZLgyLaidNPTrnM2Hd9YCsrZyTEgeh/l7fQxO790heTwTHnCyv6YnQR8Q7E6/BDc2HF+Xy1Xioz+BVCcWza9D5Wn1U7kCM9mpzMTwu+uMkzazenSCEHS+/dn8ptoDIt/wQ837pDFSlXdLu0ZJvya9Kyu0y686DRG1YYLAszKiU8pldXNGhWBzOgFAZmAnNvap7QDJmJNSJaYKkcOVP3HLQKj7G2yKUhqUPFIZ24rlqEN5u/mvoBrbVlqtyWeWbG2bX/sW4pcrMuE4Gc0wfOrYf39Co2yJ31c7DdVkGHeZthA3EEkCo5XRwqzJk9vDA7vs0BytdRcQ6CUU9DxL6V5KUiyrx5m/qmkc/t9Hh1XWNioPIYKQtztEKKHMcyncrXHj/5wcryYq11kcLdKrJNf85j4Vz0wpsW6Rgy/ejdUO2tQeOz5ghoWkDF9Tkr0Hx8b4QpfG03yKanEUp0lK5KYGGnHX506h8Lv7r3T28xJ8Ee03XgexTdYr1H1iTNCUmjwDIbpkS2Oy+v1ecggodNnj+31m/INNt4am1kr2uWt1gOK2IG9f08sOd90/21R1u+qBIWmA/dg+Fg1kxE4TMXf3v1053Dmgro+ltta3dbgcexdd3on5Qf6hAAoKeNRPRAxgN5O0Uach/iGiKf8091a2ubwjbp+ow7GX97wbKssN+BtUzTWnwnwbDWYKOXPNwWVuNkIDVmIjKr/fQwKRnQA+J89i6c/ynVPe4WOg=';
    const iv = 'AXhKSpE/B55XUQdkyCKo/A==';
    
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
