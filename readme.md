CREATE TABLE users (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(255) NOT NULL,
    phone_number NVARCHAR(15) NOT NULL UNIQUE,
    created_at DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
    updated_at DATETIMEOFFSET
);

CREATE TABLE categories (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(255) NOT NULL UNIQUE
);

CREATE INDEX idx_category_name ON categories(name);


CREATE TABLE addresses (
    id INT IDENTITY(1,1) PRIMARY KEY,
    street NVARCHAR(255),
    city NVARCHAR(255) NOT NULL,
    state NVARCHAR(255) NOT NULL,
    zip_code NVARCHAR(10) NOT NULL,
    country NVARCHAR(255) NOT NULL DEFAULT 'USA'
);

CREATE TABLE jobs (
    id INT IDENTITY(1,1) PRIMARY KEY,
    job_description NVARCHAR(255) NOT NULL,
    category_id INT NOT NULL FOREIGN KEY REFERENCES categories(id),
    date_time DATETIMEOFFSET NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    posting_fee DECIMAL(10,2),
    zip_code NVARCHAR(10) NOT NULL,
    posted_by INT NOT NULL FOREIGN KEY REFERENCES users(id),
    accepted_by INT FOREIGN KEY REFERENCES users(id),
    payment_id NVARCHAR(255),
    status NVARCHAR(255) DEFAULT 'pending',
    payment_status NVARCHAR(255) DEFAULT 'unpaid',
    address_id INT FOREIGN KEY REFERENCES addresses(id),
    payment_intent NVARCHAR(255),
    payment_transfer_id NVARCHAR(255),
    created_at DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET(),
    updated_at DATETIMEOFFSET
);

CREATE INDEX idx_job_status ON jobs(status);
CREATE INDEX idx_job_date_time ON jobs(date_time);
CREATE INDEX idx_job_category_id ON jobs(category_id);

CREATE TABLE chat_sessions (
    id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    job_id INT FOREIGN KEY REFERENCES jobs(id),
    job_type NVARCHAR(255),
    user_id INT NOT NULL FOREIGN KEY REFERENCES users(id),
    created_at DATETIMEOFFSET NOT NULL DEFAULT SYSDATETIMEOFFSET()
);

CREATE INDEX idx_chat_session_id ON chat_sessions(id);



