
        document.getElementById('contactForm').addEventListener('submit', function(event) {
            event.preventDefault();
            
            // 这里可以添加表单提交逻辑
            alert('感谢您的留言，我们会尽快回复您！');
            this.reset();
        });
    