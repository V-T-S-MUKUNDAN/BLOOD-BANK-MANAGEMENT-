
import mysql.connector
from mysql.connector import Error, pooling
import re
from typing import List, Optional
import datetime

# Database connection pooling
try:
    db_pool = mysql.connector.pooling.MySQLConnectionPool(
        pool_name="mypool",
        pool_size=5,
        pool_reset_session=True,
        host="localhost",
        user="root",
        password="Mugi@VTS#3092005",
        database="blood_bank_db"
    )
    print("Database connection pool created successfully.")
except Error as e:
    print(f"Error creating database connection pool: {e}")
    db_pool = None # Set pool to None if creation fails

app = FastAPI(title="Blood Bank API")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows all origins
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods
    allow_headers=["*"], # Allows all headers
)

# --- Pydantic Models ---

class BaseRecord(BaseModel):
    name: str = Field(..., min_length=1)
    age: int = Field(..., ge=18, le=65)
    gender: str = Field(..., min_length=1)
    blood_group: str = Field(..., min_length=1)
    contact_number: str = Field(..., pattern=r'^[0-9]{10}$')

class DonorCreate(BaseRecord):
    pass

class Donor(BaseRecord):
    donor_id: int

class RecipientCreate(BaseRecord):
    pass

class Recipient(BaseRecord):
    recipient_id: int

class BloodInventoryItem(BaseModel):
    inventory_id: int
    blood_group: str
    quantity: int
    last_updated: Optional[datetime.datetime] = None # Make optional or provide default

class StaffCreate(BaseModel):
    name: str = Field(..., min_length=1)
    role: str = Field(..., min_length=1)
    contact_number: str = Field(..., pattern=r'^[0-9]{10}$')

class Staff(StaffCreate):
    staff_id: int

class DonationCreate(BaseModel):
    donor_id: int
    donation_date: datetime.date

class Donation(DonationCreate):
    donation_id: int

class TransfusionCreate(BaseModel):
    recipient_id: int
    transfusion_date: datetime.date

class Transfusion(TransfusionCreate):
    transfusion_id: int

class BloodTestCreate(BaseModel):
    donor_id: int
    test_date: datetime.date
    result: str = Field(..., min_length=1)

class BloodTest(BloodTestCreate):
    test_id: int

class ReportData(BaseModel):
    donors: List[Donor]
    recipients: List[Recipient]
    inventory: List[BloodInventoryItem]


# --- Database Dependency ---

def get_db_connection():
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database service unavailable")
    try:
        conn = db_pool.get_connection()
        if conn.is_connected():
            return conn
        else:
            # Handle case where connection from pool is not active
            raise HTTPException(status_code=503, detail="Failed to get valid database connection")
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

# --- Utility Functions (Validation already handled by Pydantic) ---
# validate_contact and validate_age are replaced by Pydantic model validation

# --- API Endpoints ---

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Blood Bank API"}

@app.post("/donors/", response_model=Donor, status_code=201)
async def create_donor(donor: DonorCreate, conn: mysql.connector.MySQLConnection = Depends(get_db_connection)):
    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO Donors (name, age, gender, blood_group, contact_number)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            donor.name, donor.age, donor.gender, donor.blood_group, donor.contact_number
        ))
        conn.commit()
        donor_id = cursor.lastrowid
        cursor.close()
        return Donor(donor_id=donor_id, **donor.dict())
    except Error as e:
        conn.rollback() # Rollback in case of error
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if conn and conn.is_connected():
            conn.close()

@app.post("/recipients/", response_model=Recipient, status_code=201)
async def create_recipient(recipient: RecipientCreate, conn: mysql.connector.MySQLConnection = Depends(get_db_connection)):
    # Note: Original Flask code checked if request.is_json. FastAPI handles this automatically.
    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO Recipients (name, age, gender, blood_group, contact_number)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            recipient.name, recipient.age, recipient.gender, recipient.blood_group, recipient.contact_number
        ))
        conn.commit()
        recipient_id = cursor.lastrowid
        cursor.close()
        return Recipient(recipient_id=recipient_id, **recipient.dict())
    except Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if conn and conn.is_connected():
            conn.close()

@app.get("/blood_inventory/", response_model=List[BloodInventoryItem])
async def get_blood_inventory(conn: mysql.connector.MySQLConnection = Depends(get_db_connection)):
    try:
        cursor = conn.cursor(dictionary=True) # Fetch as dict
        cursor.execute("SELECT inventory_id, blood_group, quantity, last_updated FROM Blood_Inventory")
        inventory_data = cursor.fetchall()
        cursor.close()
        # Validate fetched data with Pydantic model
        validated_data = [BloodInventoryItem(**item) for item in inventory_data]
        return validated_data
    except ValidationError as ve:
         raise HTTPException(status_code=500, detail=f"Data validation error: {str(ve)}")
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.post("/staff/", response_model=Staff, status_code=201)
async def add_staff(staff: StaffCreate, conn: mysql.connector.MySQLConnection = Depends(get_db_connection)):
    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO Staff (name, role, contact_number)
            VALUES (%s, %s, %s)
        """
        cursor.execute(query, (staff.name, staff.role, staff.contact_number))
        conn.commit()
        staff_id = cursor.lastrowid
        cursor.close()
        return Staff(staff_id=staff_id, **staff.dict())
    except Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if conn and conn.is_connected():
            conn.close()

@app.post("/donations/", response_model=Donation, status_code=201)
async def record_donation(donation: DonationCreate, conn: mysql.connector.MySQLConnection = Depends(get_db_connection)):
    try:
        cursor = conn.cursor()
        # Potential check: Verify donor_id exists in Donors table (optional)
        query = """
            INSERT INTO Donations (donor_id, donation_date)
            VALUES (%s, %s)
        """
        cursor.execute(query, (donation.donor_id, donation.donation_date))
        conn.commit()
        donation_id = cursor.lastrowid
        cursor.close()
        return Donation(donation_id=donation_id, **donation.dict())
    except Error as e:
        conn.rollback()
        # Check for specific errors like foreign key constraint violation
        if "FOREIGN KEY (`donor_id`)" in str(e):
             raise HTTPException(status_code=404, detail=f"Donor with ID {donation.donor_id} not found.")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.post("/transfusions/", response_model=Transfusion, status_code=201)
async def record_transfusion(transfusion: TransfusionCreate, conn: mysql.connector.MySQLConnection = Depends(get_db_connection)):
    try:
        cursor = conn.cursor()
        # Potential check: Verify recipient_id exists
        query = """
            INSERT INTO Transfusions (recipient_id, transfusion_date)
            VALUES (%s, %s)
        """
        cursor.execute(query, (transfusion.recipient_id, transfusion.transfusion_date))
        conn.commit()
        transfusion_id = cursor.lastrowid
        cursor.close()
        return Transfusion(transfusion_id=transfusion_id, **transfusion.dict())
    except Error as e:
        conn.rollback()
        if "FOREIGN KEY (`recipient_id`)" in str(e):
             raise HTTPException(status_code=404, detail=f"Recipient with ID {transfusion.recipient_id} not found.")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.post("/blood_tests/", response_model=BloodTest, status_code=201)
async def record_blood_test(test: BloodTestCreate, conn: mysql.connector.MySQLConnection = Depends(get_db_connection)):
    try:
        cursor = conn.cursor()
         # Potential check: Verify donor_id exists
        query = """
            INSERT INTO Blood_Tests (donor_id, test_date, result)
            VALUES (%s, %s, %s)
        """
        cursor.execute(query, (test.donor_id, test.test_date, test.result))
        conn.commit()
        test_id = cursor.lastrowid
        cursor.close()
        return BloodTest(test_id=test_id, **test.dict())
    except Error as e:
        conn.rollback()
        if "FOREIGN KEY (`donor_id`)" in str(e):
             raise HTTPException(status_code=404, detail=f"Donor with ID {test.donor_id} not found.")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if conn and conn.is_connected():
            conn.close()

@app.get("/reports/", response_model=ReportData)
async def get_reports(conn: mysql.connector.MySQLConnection = Depends(get_db_connection)):
    try:
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT donor_id, name, age, gender, blood_group, contact_number FROM Donors")
        donors_raw = cursor.fetchall()

        cursor.execute("SELECT recipient_id, name, age, gender, blood_group, contact_number FROM Recipients")
        recipients_raw = cursor.fetchall()

        cursor.execute("SELECT inventory_id, blood_group, quantity, last_updated FROM Blood_Inventory")
        inventory_raw = cursor.fetchall()

        cursor.close()

        # Validate data using Pydantic models
        donors = [Donor(**d) for d in donors_raw]
        recipients = [Recipient(**r) for r in recipients_raw]
        inventory = [BloodInventoryItem(**i) for i in inventory_raw]

        return ReportData(donors=donors, recipients=recipients, inventory=inventory)
    except ValidationError as ve:
         raise HTTPException(status_code=500, detail=f"Report data validation error: {str(ve)}")
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error fetching reports: {str(e)}")
    finally:
        if conn and conn.is_connected():
            conn.close()

# --- Main Execution Guard ---
# To run the app, use: uvicorn main:app --reload
# Ensure uvicorn and fastapi are installed: pip install fastapi uvicorn mysql-connector-python pydantic[email] python-dotenv

# Example of running with uvicorn programmatically (optional)
# if __name__ == '__main__':
#     import uvicorn
#     uvicorn.run(app, host="127.0.0.1", port=8000)

# Remove Flask-specific execution
# if __name__ == '__main__':
#     app.run(debug=True)
