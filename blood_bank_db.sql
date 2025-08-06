CREATE DATABASE blood_bank_db;

USE blood_bank_db;

CREATE TABLE Donors (
    donor_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    age INT,
    gender VARCHAR(10),
    blood_group VARCHAR(5),
    contact_number VARCHAR(20)
);

CREATE TABLE Recipients (
    recipient_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    age INT,
    gender VARCHAR(10),
    blood_group VARCHAR(5),
    contact_number VARCHAR(20)
);

CREATE TABLE Blood_Inventory (
    blood_id INT AUTO_INCREMENT PRIMARY KEY,
    blood_group VARCHAR(5),
    quantity INT
);

CREATE TABLE Staff (
    staff_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    role VARCHAR(50),
    contact_number VARCHAR(20)
);

CREATE TABLE Donations (
    donation_id INT AUTO_INCREMENT PRIMARY KEY,
    donor_id INT,
    donation_date DATE,
    FOREIGN KEY (donor_id) REFERENCES Donors(donor_id)
);

CREATE TABLE Transfusions (
    transfusion_id INT AUTO_INCREMENT PRIMARY KEY,
    recipient_id INT,
    transfusion_date DATE,
    FOREIGN KEY (recipient_id) REFERENCES Recipients(recipient_id)
);

CREATE TABLE Blood_Tests (
    test_id INT AUTO_INCREMENT PRIMARY KEY,
    donor_id INT,
    test_date DATE,
    result VARCHAR(50),
    FOREIGN KEY (donor_id) REFERENCES Donors(donor_id)
);

select * from donors;