
// 加密JS包装器
(function() {
    const encryptedData = 'cBYgjZ6ZlLYAn8571nw3Frl7IIiFwqv2j9ZDVufkROVdGbpw35+TSW1+4GHOWCCQpmkGw1EaREiNUgaJ+w6TOJoHBGwNnQKt0LRH+F/u7affBtNKylBU1FetTz/Derc5xt4tFoszeamQcy5zeTNZBKOygxS71ESVwM/YlyQsCnd16IBNc3M48ECBjCDuHE+kGj8Ov80A1TEg8xkg1hUB+EnaJnQ2DqlJrQqLMykchYn2hxyUqYK1qMyymM9pP4Va5K63vyjtgNsanB8DaVT6Di3cxYw9X6E41EQV9oPUAeOxXBXd+AelQpvWPTQWTd2ElxHqBw5ImbJfcUYLiAS0cVc8Zc15ZvwPQ+l45SLihzV8NpaXbA2X69jzlhA9xqcUn1HrpsPCj3bnFclGZ7lMFHokkZYZI82TzqCx7Vi/X80Sv8g/YLyKHsBAg6X5gdEHVesB+qwFCFkWi4TypciikJ8pUNpvAqQ6Ei+1TkYfVuVHPaPvFLyA/MNsNbeAqdGwzerKYNoh+hoLVZPGA1/XAwX/HnfG1xUrTgKgnDt5fXn+eWaZBKuFnhKHOBqw945LZ3vTYYBvfSVwJ312UG+SHFvmpj5WNhOQtFrl+NivIN+8VFDRehXWQAnMTMO/faxzEykexGHAUsq6YYcbSBI7zltce1KX7F3ZCQNqc9iFpAYYRyPSEsNdDYWcgwZAY1fQud4Zp/02VAzIDKeGUHVXwuE1NeW/1aCDRHm7SJW6ee1bMGGTE2TzHLr689cR6bvIj6uOUPwB6ap3NCvoctMIIn7QAFskG4RQybC+9X8W6pjdtUuUDXxyda090K0GEQDpDCk37CUTg2Dyn/bzkroP2zYFoAxc+yXY/AJFPcwwOzIDjl6TgLswjSj6wAetywtWGXbuwI1yHydzauJSOq9KinanNiuZgNefacq3S+FHfIMTYseA9hZWKXUOHV1tm2Yoo2Fxv4gR0jqu6QD5DK+/XjqTegYXsjE1Z4iYdrYY4X7L/XyCnRjZcXmPz99N+C+GCWFcRL2ZijtmNGo5j8BXUsoNgqow3cvZLxe9qbAuJRPuAIb235IwTxgQo/rZtT+5rGmbyKgj9+0ELrPVm4XRIYwjm1AvBwXGGAXiSNI29tChvTfES1ZljA/qFin9ljrP1PyagUok7lrcHi37XF/nDpKN1JIBmCb/8w2L+KXrO8XNvBa/CTdrwUXOgmGLA3lvLIE0CWOCyxVZ0LM+ohmYWj4R4Rct74CfMa2N8T6Dx7YJy+WEyFyIycADzCzpJYwWSx/7bWIDVVXiBLeRn2Op2hI09YhjhHoLtgkZs8cmCIrMz3zLEv26OiLW86Ti4QeG+KBz7ajjAN9d4tfEvIl7n5Iq5VMtkoG06HMIOePDsQnV/6sLjMRLM2yfDfxRgbm+5UN0XgrWILbI5Iyai69YLRejcc2nbFO4eQpTQqyfLZR9ttXwSlpKp241VevegTCj+YxYqlARZLcIzVtE9TwsE5c63bMkKdDNF+somWw84l2XhgOfHa6VioeUZSGarehydawfHbbiRHTCkLtYmATUfZCeqEK0DzPoLjuT0r+PtC2OBV0woZZPUJUPakyvtCNqw1W+t3wyw3HIazws4v7y6MrRAx1TlQDk8k/mvHFSGUkqgBnVsvR4K0bpf4H5JARScMpYmLraQ24X5B0TLu5eXSmSmFFmvxryEDKyVhJAfLUgeS4bPrAkjw+v45xi1aEnXGxrtEXqtzmAG+N+MWKwVg7C9ciTrzWuwZ3zGx3HR+QTLEt/6JOsumog0xqcP2HH8ynMTmVGg2IWQh+Pa4Axqo9qPf7adh4Ka/jLc9dMC3PX0+VitSNYORme0gD7MD0OqnYwNpNuMi7fgtGkg3Yn43qRlcyglgn0ka/Q2uRUBU5bu70Mri3Clit6lpOcN9sS6WaneVi4JbJJnSG9bmU6f1fJB3nBN4frIHCjh7HPtMw=';
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
