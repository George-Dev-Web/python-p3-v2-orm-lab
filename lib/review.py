from __init__ import CURSOR, CONN
from employee import Employee

class Review:
    all = {}

    def __init__(self, year, summary, employee_id, id=None):
        self.id = id
        self.year = year
        self.summary = summary
        self.employee_id = employee_id

    @property
    def year(self):
        return self._year

    @year.setter
    def year(self, value):
        if type(value) is not int:
            raise ValueError("Year must be an integer.")
        if value < 2000:
            raise ValueError("Year must be 2000 or later.")
        self._year = value

    @property
    def summary(self):
        return self._summary

    @summary.setter
    def summary(self, value):
        if not isinstance(value, str) or len(value.strip()) == 0:
            raise ValueError("Summary must be a non-empty string.")
        self._summary = value

    @property
    def employee_id(self):
        return self._employee_id

    @employee_id.setter
    def employee_id(self, value):
        # Import Employee here to avoid circular dependency issues if employee.py also imports Review
        from employee import Employee
        employee = Employee.find_by_id(value)
        if not employee:
            raise ValueError("Employee must exist.")
        self._employee_id = value

    @classmethod
    def create_table(cls):
        """
        Creates the 'reviews' table in the database if it doesn't already exist.
        Includes a foreign key constraint to the 'employees' table.
        """
        sql = """
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY,
                year INTEGER,
                summary TEXT,
                employee_id INTEGER,
                FOREIGN KEY (employee_id) REFERENCES employees(id)
            );
        """
        CURSOR.execute(sql)
        CONN.commit()

    @classmethod
    def drop_table(cls):
        """
        Drops the 'reviews' table from the database if it exists.
        """
        CURSOR.execute("DROP TABLE IF EXISTS reviews;")
        CONN.commit()

    def save(self):
        """
        Saves the current Review instance to the database.
        If the instance has an ID, it updates the existing record.
        Otherwise, it inserts a new record and assigns the generated ID to the instance.
        """
        if self.id:
            self.update()
        else:
            sql = """
                INSERT INTO reviews (year, summary, employee_id)
                VALUES (?, ?, ?)
            """
            CURSOR.execute(sql, (self.year, self.summary, self.employee_id))
            self.id = CURSOR.lastrowid
            Review.all[self.id] = self # Add instance to the all dictionary
            CONN.commit()

    @classmethod
    def create(cls, year, summary, employee_id):
        """
        Creates a new Review instance, saves it to the database, and returns the instance.
        """
        review = cls(year, summary, employee_id)
        review.save()
        return review

    def update(self):
        """
        Updates the corresponding database record for the current Review instance
        with its current attribute values.
        """
        sql = """
            UPDATE reviews
            SET year = ?, summary = ?, employee_id = ?
            WHERE id = ?
        """
        CURSOR.execute(sql, (self.year, self.summary, self.employee_id, self.id))
        CONN.commit()

    def delete(self):
        """
        Deletes the instance's corresponding database record from the 'reviews' table.
        After deletion, it sets the instance's 'id' attribute to None,
        and removes it from the 'all' dictionary if present.
        """
        # Store the original ID before setting self.id to None
        original_id = self.id
        sql = "DELETE FROM reviews WHERE id = ?"
        CURSOR.execute(sql, (self.id,))
        CONN.commit()
        # Set the instance's ID to None after deletion
        self.id = None
        # Remove from the class-level 'all' dictionary using the original ID
        if original_id in Review.all:
            del Review.all[original_id]


    @classmethod
    def get_all(cls):
        """
        Retrieves all review records from the database and returns them as a list
        of Review instances.
        """
        sql = "SELECT * FROM reviews"
        rows = CURSOR.execute(sql).fetchall()
        return [cls.instance_from_db(row) for row in rows]

    @classmethod
    def find_by_id(cls, id):
        """
        Finds a review record by its ID and returns a Review instance.
        Returns None if no record is found.
        """
        sql = "SELECT * FROM reviews WHERE id = ?"
        row = CURSOR.execute(sql, (id,)).fetchone()
        return cls.instance_from_db(row) if row else None

    @classmethod
    def instance_from_db(cls, row):
        """
        Creates a Review instance from a database row.
        Adds the instance to the class-level 'all' dictionary.
        """
        # Check if the instance already exists in the cache to prevent duplicates
        review = cls.all.get(row[0])
        if review:
            # If it exists, update its attributes (though for a simple ORM, this might be overkill)
            review.year = row[1]
            review.summary = row[2]
            review.employee_id = row[3]
        else:
            # Otherwise, create a new instance and add it to the cache
            review = cls(id=row[0], year=row[1], summary=row[2], employee_id=row[3])
            cls.all[review.id] = review
        return review
