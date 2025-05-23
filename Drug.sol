// SPDX-License-Identifier: MIT
pragma solidity >=0.8.11 <0.9.0;

contract Drug {
    // Events
    event UserAdded(address indexed user, string username, string role);
    event UserUpdated(address indexed user, string username, string role);
    event UserDeactivated(address indexed user);
    event DrugAdded(bytes32 indexed drugId, string name, string batchNumber);
    event DrugUpdated(bytes32 indexed drugId, string status);
    event DrugStatusUpdated(bytes32 indexed drugId, string status, string location);
    event DrugTraceAdded(bytes32 indexed drugId, string action, string actor, uint256 timestamp);
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    // Structs
    struct User {
        string username;
        string email;
        string role;
        string blockchainAddress;
        uint256 registeredAt;
        uint256 updatedAt;
        bool isActive;
    }

    struct DrugInfo {
        string name;
        string manufacturer;
        string batchNumber;
        uint256 manufacturingDate;
        uint256 expiryDate;
        uint256 quantity;
        string description;
        string status;
        uint256 createdAt;
        uint256 updatedAt;
        bool isActive;
    }

    struct DrugTrace {
        string action;
        string actor;
        string location;
        uint256 quantity;
        string notes;
        uint256 timestamp;
    }

    // State variables
    address public owner;
    mapping(address => User) public users;
    mapping(bytes32 => DrugInfo) public drugs;
    mapping(bytes32 => mapping(uint256 => DrugTrace)) public drugTraces; // drugId => traceIndex => trace
    mapping(bytes32 => uint256) public drugTraceCount; // drugId => number of traces
    mapping(string => bytes32) public batchToDrugId;
    mapping(address => mapping(uint256 => bytes32)) public userDrugs; // user => index => drugId
    mapping(address => uint256) public userDrugCount; // user => number of drugs

    // Constants
    uint256 public constant MAX_STRING_LENGTH = 200;
    uint256 public constant MAX_QUANTITY = 1000000;
    uint256 public constant MAX_TRACES_PER_DRUG = 1000;
    uint256 public constant MAX_DRUGS_PER_USER = 1000;

    // Modifiers
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }

    modifier validString(string memory str) {
        require(bytes(str).length > 0, "String cannot be empty");
        require(bytes(str).length <= MAX_STRING_LENGTH, "String too long");
        _;
    }

    modifier validQuantity(uint256 quantity) {
        require(quantity > 0, "Quantity must be greater than 0");
        require(quantity <= MAX_QUANTITY, "Quantity exceeds maximum limit");
        _;
    }

    modifier userExists(address userAddress) {
        require(users[userAddress].registeredAt > 0, "User does not exist");
        require(users[userAddress].isActive, "User is not active");
        _;
    }

    modifier drugExists(bytes32 drugId) {
        require(drugs[drugId].createdAt > 0, "Drug does not exist");
        require(drugs[drugId].isActive, "Drug is not active");
        _;
    }

    // Constructor
    constructor() {
        owner = msg.sender;
        emit OwnershipTransferred(address(0), owner);
    }

    // User management functions
    function addUser(
        address userAddress,
        string memory username,
        string memory email,
        string memory role,
        string memory blockchainAddress
    ) public onlyOwner validString(username) validString(email) validString(role) {
        require(users[userAddress].registeredAt == 0, "User already exists");
        
        users[userAddress] = User({
            username: username,
            email: email,
            role: role,
            blockchainAddress: blockchainAddress,
            registeredAt: block.timestamp,
            updatedAt: block.timestamp,
            isActive: true
        });

        emit UserAdded(userAddress, username, role);
    }

    function updateUser(
        address userAddress,
        string memory username,
        string memory email,
        string memory role,
        string memory blockchainAddress
    ) public onlyOwner userExists(userAddress) validString(username) validString(email) validString(role) {
        User storage user = users[userAddress];
        user.username = username;
        user.email = email;
        user.role = role;
        user.blockchainAddress = blockchainAddress;
        user.updatedAt = block.timestamp;

        emit UserUpdated(userAddress, username, role);
    }

    function getUser(address userAddress) public view returns (User memory) {
        require(users[userAddress].registeredAt > 0, "User does not exist");
        return users[userAddress];
    }

    // Drug management functions
    function addDrug(
        string memory name,
        string memory batchNumber,
        uint256 manufacturingDate,
        uint256 expiryDate,
        uint256 quantity,
        string memory description
    ) public userExists(msg.sender) validString(name) validString(batchNumber) validString(description) validQuantity(quantity) {
        require(manufacturingDate < expiryDate, "Invalid dates");
        require(manufacturingDate <= block.timestamp, "Manufacturing date in future");
        require(batchToDrugId[batchNumber] == bytes32(0), "Batch number already exists");
        require(userDrugCount[msg.sender] < MAX_DRUGS_PER_USER, "Too many drugs for user");

        bytes32 drugId = keccak256(abi.encodePacked(batchNumber, block.timestamp));
        
        drugs[drugId] = DrugInfo({
            name: name,
            manufacturer: users[msg.sender].username,
            batchNumber: batchNumber,
            manufacturingDate: manufacturingDate,
            expiryDate: expiryDate,
            quantity: quantity,
            description: description,
            status: "production",
            createdAt: block.timestamp,
            updatedAt: block.timestamp,
            isActive: true
        });

        batchToDrugId[batchNumber] = drugId;
        userDrugs[msg.sender][userDrugCount[msg.sender]] = drugId;
        userDrugCount[msg.sender]++;

        emit DrugAdded(drugId, name, batchNumber);
    }

    function updateDrug(
        bytes32 drugId,
        string memory name,
        string memory description,
        uint256 quantity
    ) public drugExists(drugId) validString(name) validString(description) validQuantity(quantity) {
        require(keccak256(bytes(drugs[drugId].manufacturer)) == keccak256(bytes(users[msg.sender].username)), 
                "Only manufacturer can update drug");
        
        DrugInfo storage drug = drugs[drugId];
        drug.name = name;
        drug.description = description;
        drug.quantity = quantity;
        drug.updatedAt = block.timestamp;

        emit DrugUpdated(drugId, drug.status);
    }

    function updateDrugStatus(
        bytes32 drugId,
        string memory status,
        string memory location,
        uint256 quantity,
        string memory notes
    ) public drugExists(drugId) validString(status) validString(location) validQuantity(quantity) validString(notes) {
        require(drugTraceCount[drugId] < MAX_TRACES_PER_DRUG, "Too many traces for drug");
        
        DrugInfo storage drug = drugs[drugId];
        drug.status = status;
        drug.updatedAt = block.timestamp;

        uint256 traceIndex = drugTraceCount[drugId];
        drugTraces[drugId][traceIndex] = DrugTrace({
            action: status,
            actor: users[msg.sender].username,
            location: location,
            quantity: quantity,
            notes: notes,
            timestamp: block.timestamp
        });
        drugTraceCount[drugId]++;

        emit DrugStatusUpdated(drugId, status, location);
        emit DrugTraceAdded(drugId, status, users[msg.sender].username, block.timestamp);
    }

    function getDrug(bytes32 drugId, uint256 startTrace, uint256 limit) 
        public 
        view 
        drugExists(drugId) 
        returns (DrugInfo memory, DrugTrace[] memory) 
    {
        require(startTrace < drugTraceCount[drugId], "Invalid start trace");
        require(limit > 0 && limit <= 50, "Invalid limit");
        
        uint256 endTrace = startTrace + limit;
        if (endTrace > drugTraceCount[drugId]) {
            endTrace = drugTraceCount[drugId];
        }
        
        DrugTrace[] memory traces = new DrugTrace[](endTrace - startTrace);
        for (uint256 i = startTrace; i < endTrace; i++) {
            traces[i - startTrace] = drugTraces[drugId][i];
        }
        
        return (drugs[drugId], traces);
    }

    function getDrugByBatch(string memory batchNumber, uint256 startTrace, uint256 limit) 
        public 
        view 
        returns (DrugInfo memory, DrugTrace[] memory) 
    {
        bytes32 drugId = batchToDrugId[batchNumber];
        require(drugId != bytes32(0), "Drug not found");
        return getDrug(drugId, startTrace, limit);
    }

    function getUserDrugs(address userAddress, uint256 start, uint256 limit) 
        public 
        view 
        userExists(userAddress) 
        returns (bytes32[] memory) 
    {
        require(start < userDrugCount[userAddress], "Invalid start");
        require(limit > 0 && limit <= 50, "Invalid limit");
        
        uint256 end = start + limit;
        if (end > userDrugCount[userAddress]) {
            end = userDrugCount[userAddress];
        }
        
        bytes32[] memory userDrugsList = new bytes32[](end - start);
        for (uint256 i = start; i < end; i++) {
            userDrugsList[i - start] = userDrugs[userAddress][i];
        }
        
        return userDrugsList;
    }

    // Emergency functions
    function deactivateUser(address userAddress) public onlyOwner userExists(userAddress) {
        users[userAddress].isActive = false;
        emit UserDeactivated(userAddress);
    }

    function deactivateDrug(bytes32 drugId) public onlyOwner drugExists(drugId) {
        drugs[drugId].isActive = false;
        emit DrugUpdated(drugId, "deactivated");
    }

    function transferOwnership(address newOwner) public onlyOwner {
        require(newOwner != address(0), "Invalid new owner");
        address oldOwner = owner;
        owner = newOwner;
        emit OwnershipTransferred(oldOwner, newOwner);
    }
}