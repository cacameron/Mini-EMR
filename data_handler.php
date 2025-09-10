<?php
	class DataHandler { 
		// Properties  
		private $db_conn; 
		
		// Methods
		public function __construct() { 
			//Create the database connection
			$this->db_conn = MySQLi_connect(
   				"localhost", //Server Name
   				"taus_web_user", //Username
   				"NkD.-z)X0v1XoyWx", //Password
   				"taus_data" //Database Name
			);  
			//Test the connection
			if (MySQLi_connect_errno()) {
				die("Connection failed: " . MySQLi_connect_error());
			}
		}
		
		public function get_student($s_id) {
				//Stored procedure to run
   				$query = "CALL sp_get_student('".$s_id."')";
   				
				//Stored procedure preparation
   				$exec_query = MySQLi_query($this->db_conn, $query);
   	
   				//Fetching result from database
   				$q_results = MySQLi_fetch_array($exec_query);
   				
				return $q_results;
		}

		public function get_students($last_name) {
			//Declare the array variable
			$my_arr = array();

			//Stored procedure to run
			$query = "CALL sp_get_students('".$last_name."')";
			   
			//Stored procedure preparation
			$exec_query = MySQLi_query($this->db_conn, $query);
   
			//Loop through the results, building the array of associative arrays
			while ($row = mysqli_fetch_array($exec_query)) {
				$my_arr[] = $row;
			}
			   
			return $my_arr;
		}
		public function add_student($first_name, $mi, $last_name, $photo_id) {
			$message = "";

			//Stored procedure to run
			$query = "CALL sp_insert_student('".$first_name."','".$mi.",'".$last_name."','".$photo_id."')";
			   
			//Stored procedure preparation
			$ExecQuery = MySQLi_query($this->db_conn, $query);
   
			//Loop through the results, building the array of associative arrays
			if ($ExecQuery == '1')
			{
				$message = "Success!";
			}
			}
			else
			{
				$message = "Save Operation Failed";
			}
			   
			return $message;
		}
	}
	
?>