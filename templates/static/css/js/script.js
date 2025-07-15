document.addEventListener('DOMContentLoaded', function() {
    // DOM এলিমেন্ট সিলেক্ট
    const spinBtn = document.getElementById('spin-btn');
    const wheel = document.getElementById('wheel');
    const rewardPopup = document.getElementById('reward-popup');
    const rewardAmount = document.getElementById('reward-amount');
    const specialOffer = document.getElementById('special-offer');
    const closeBtn = document.querySelector('.close');
    const watchAdBtn = document.getElementById('watch-ad-btn');
    const installOfferBtn = document.getElementById('install-offer-btn');
    const withdrawBtn = document.getElementById('withdraw-btn');
    const withdrawAmount = document.getElementById('withdraw-amount');
    const upiId = document.getElementById('upi-id');
    const spinsLeft = document.getElementById('spins-left');
    const userBalance = document.getElementById('user-balance');
    
    let isSpinning = false;
    let currentRotation = 0;
    
    // স্পিন বাটন ক্লিক ইভেন্ট
    spinBtn.addEventListener('click', function() {
        if (isSpinning) return;
        
        isSpinning = true;
        spinBtn.disabled = true;
        
        // র্যান্ডম রোটেশন (5-10 রোটেশন)
        const spinDegrees = 1800 + Math.floor(Math.random() * 1800);
        currentRotation += spinDegrees;
        
        wheel.style.transform = `rotate(${currentRotation}deg)`;
        
        // স্পিন শেষ হলে
        setTimeout(function() {
            // সার্ভারে স্পিন রিকোয়েস্ট পাঠান
            fetch('/spin', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({})
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert(data.error);
                } else {
                    // রিওয়ার্ড শো করুন
                    rewardAmount.textContent = `₹${data.reward.toFixed(2)}`;
                    
                    // স্পেশাল অফার (5ম এবং 10ম স্পিনে)
                    if (data.is_special) {
                        specialOffer.style.display = 'block';
                    } else {
                        specialOffer.style.display = 'none';
                    }
                    
                    rewardPopup.style.display = 'flex';
                    
                    // ইউজার ব্যালেন্স আপডেট করুন
                    updateUserBalance();
                }
                
                isSpinning = false;
                spinBtn.disabled = false;
            })
            .catch(error => {
                console.error('Error:', error);
                isSpinning = false;
                spinBtn.disabled = false;
            });
        }, 3000);
    });
    
    // উইথড্রয়াল বাটন ক্লিক ইভেন্ট
    withdrawBtn.addEventListener('click', function() {
        const amount = parseFloat(withdrawAmount.value);
        const upi = upiId.value.trim();
        
        if (!amount || amount < 5) {
            alert('Minimum withdrawal amount is ₹5');
            return;
        }
        
        if (!upi) {
            alert('Please enter your UPI ID');
            return;
        }
        
        fetch('/withdraw', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                amount: amount,
                upi_id: upi
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
            } else {
                alert(data.message);
                updateUserBalance();
                withdrawAmount.value = '';
                upiId.value = '';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Withdrawal request failed');
        });
    });
    
    // পপআপ ক্লোজ বাটন
    closeBtn.addEventListener('click', function() {
        rewardPopup.style.display = 'none';
    });
    
    // ওয়াচ এড বাটন
    watchAdBtn.addEventListener('click', function() {
        // এখানে AdMob ইন্টিগ্রেশন যোগ করুন
        alert('Ad played successfully! Reward claimed.');
        rewardPopup.style.display = 'none';
    });
    
    // ইনস্টল অফার বাটন
    installOfferBtn.addEventListener('click', function() {
        // এখানে অ্যাপ ইন্সটলেশন রিডাইরেক্ট করুন
        alert('Redirecting to app installation...');
        rewardPopup.style.display = 'none';
    });
    
    // ইউজার ডেটা আপডেট ফাংশন
    function updateUserBalance() {
        fetch('/user-data')
        .then(response => response.json())
        .then(data => {
            userBalance.textContent = `Balance: ₹${data.balance.toFixed(2)}`;
            spinsLeft.textContent = `Spins left today: ${20 - data.spins_today}`;
            
            // যদি স্পিন লিমিট শেষ হয়ে যায়
            if (data.spins_today >= 20) {
                spinBtn.disabled = true;
                spinBtn.textContent = 'Daily Limit Reached';
            }
        });
    }
    
    // ইনিশিয়াল ইউজার ডেটা লোড
    updateUserBalance();
    
    // পেজ ভিজিবিলিটি চেক - যদি ইউজার ট্যাব চেঞ্জ করে
    document.addEventListener('visibilitychange', function() {
        if (document.visibilityState === 'visible') {
            updateUserBalance();
        }
    });
});sc
