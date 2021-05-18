pragma solidity ^0.4.23;

contract Ownable {
  address public owner;


  event OwnershipRenounced(address indexed previousOwner);
  event OwnershipTransferred(
    address indexed previousOwner,
    address indexed newOwner
  );


  /**
   * @dev The Ownable constructor sets the original `owner` of the contract to the sender
   * account.
   */
  constructor() public {
    owner = msg.sender;
  }

  /**
   * @dev Throws if called by any account other than the owner.
   */
  modifier onlyOwner() {
    require(msg.sender == owner);
    _;
  }

  // As below - A Soul cannot transfer their profile nor renounceOwnership (but they can delete the contract)


  /**
   * @dev Allows the current owner to transfer control of the contract to a newOwner.
   * @param newOwner The address to transfer ownership to.

  function transferOwnership(address newOwner) public onlyOwner {
    require(newOwner != address(0));
    emit OwnershipTransferred(owner, newOwner);
    owner = newOwner;
  }
  */

  /**
   * @dev Allows the current owner to relinquish control of the contract.

  function renounceOwnership() public onlyOwner {
    emit OwnershipRenounced(owner);
    owner = address(0);
  }
  */

}







contract runitprofile is Ownable {
  using SafeMath for uint256;

// owner set via ownable constructor to deployer
// Run.it has 'Souls' not 'Users'.. they own their own data.


string private fname;
string private lname;
string private nickname;
string private gender;
uint256 private phone;
string private nationality;

// Soul can be Athlete, Fan, Sponsor, Organizer, Content generator, Partner .. many roles at same or differing times
string public rolecodes;  // A/F/S/O/C/P

// demo, behavioral, interests
// can be kept on a tiny cost hedera file or pinned to IPFS for PoC / pre-production
// hedera files, like SCs are on Hedera to ABFT math defined level of security. - the highest known.

// mapping(address => uint256) hedera interests file; // for use later for PoC .. maybe keep interest keywords on a hedera file - cheaper in GAS

// Likes and interests - PoC small interest selection for demo purposes. 'categories to choose from or indexes'.

string private interest1;
string private interest2;
string private interest3;


// openness preferences- so RUN.it can  use to MATCH not to SHARE.

bool public demographic;
boon public behavioral;
bool public interests;

uint256 public sponsorslevel;
uint256 public grpsponsorslevel;

//  etc.. more core details as model fleshes out.

address public runitaccountid;

address public platformaddress;

bool public kycapproved;           //  set true or false - after 3rd prty plugin.


// Sponsor exposure measure 0 - 10 0= none, 3 low, 5 medium, 10 high  to maximize rewards.


// current until refreshed by call to Run.it token contract

uint256 private runittokenbal;




  constructor(string _fname, string _lname, string _nickname, uint256 _phone, string _nationality, address _platformaddress) public {

// Run.it account is same as their hedera public key/assigned Account
// impersonation is IMPOSSIBLE if friends aware of the public key and Run.it account# for this Soul

    runitaccountid = msg.sender;
    platformaddress = _platformaddress;

    fname = _fname;
    lname = _lname;
    nickname = _nickname;
    phone = _phone;
    nationality = _nationality;

    kycapproved = true;


  }



// Events broadcast to ledger as public but anonymous receipt, if needs be.


 event Profilecreated(
    address smartcontractid
    );

 event Profileupdated(
   address runitaccountid
    );

  event Interestsupdated(
    address runitaccountid
     );

  event Opennessupdated(
   address runitaccountid
    );


// custom Modifiers

  modifier onlyrunitandpermission() {
    require((sponsorslevel > 0 || grpsponsorslevel > 0) && msg.sender == platformaddress);
    _;
  }

    // getters for Owner only!

  function getfname() view onlyOwner public returns(string) {

    return fname;
  }


  function getlname() view onlyOwner public returns(string) {

    return lname;
  }

  function getnickname() view onlyOwner public returns(string) {

    return nickname;
  }


  function getphone() view onlyOwner public returns(uint256) {

    return phone;
  }


  function getnationality() view onlyOwner public returns(string) {

    return nationality;
  }

// only owner can view these

  function getinterest1() view onlyOwner public returns(string) {

    return interest1;
  }


  function getinterest2() view onlyOwner public returns(string) {

    return interest2;
  }


  function getinterest3() view onlyOwner public returns(string) {

    return interest3;
  }

// only JOYN can see these - for matching purposes IF they have profile openness permission - TBD on degree of/ granularity
// this will a re-write for an array of interest.. more interests more gas it will cost user to maintain - micro cents!
// this will also apply to profile getter methods for MvP later on .. for demo and  behaviorial

    function runitgetinterest1() view onlyrunitandpermission public returns(string) {

      return interest1;
    }


    function runitgetinterest2() view onlyrunitandpermission public returns(string) {

      return interest2;
    }


    function runitgetinterest3() view onlyrunitandpermission public returns(string) {

      return interest3;
    }


 // update profile by Soul only. ie contract owner.

  function updateprofile (string _fname, string _lname, string _nickname, uint256 _phone, string _nationality)  public  onlyOwner{

    fname = _fname;
    lname = _lname;
    nickname = _nickname;
    phone = _phone;
    nationality = _nationality;

  }

  // ditto TBD


    function updateinterests(string _interest1, string _interest2, string _interest3, bool _demo, bool _behav, bool _inter, uint256 _sponsorslevel, uint256 _grpsponsorslevel) public onlyOwner{

        // limited for this purpose - expanded as a hedera encrypted bytcode file later.
        // code is interpreted in the DApp

      interest1 = _interest1;
      interest2 = _interest2;
      interest3 = _interest3;

      demographic = _demo;
      behavioral = _behav;
      interests = _inter;

      sponsorslevel = _sponsorslevel;
      grpsponsorslevel = _grpsponsorslevel;

    }



  function removeprofile() public onlyOwner{

    // selfdestruct profile smart contract by the Run.it Soul only.

    selfdestruct(this);


 }



}


library SafeMath {

  /**
  * @dev Multiplies two numbers, throws on overflow.
  */
  function mul(uint256 a, uint256 b) internal pure returns (uint256) {
    if (a == 0) {
      return 0;
    }
    uint256 c = a * b;
    assert(c / a == b);
    return c;
  }

  /**
  * @dev Integer division of two numbers, truncating the quotient.
  */
  function div(uint256 a, uint256 b) internal pure returns (uint256) {
    // assert(b > 0); // Solidity automatically throws when dividing by 0
    uint256 c = a / b;
    // assert(a == b * c + a % b); // There is no case in which this doesn't hold
    return c;
  }

  /**
  * @dev Subtracts two numbers, throws on overflow (i.e. if subtrahend is greater than minuend).
  */
  function sub(uint256 a, uint256 b) internal pure returns (uint256) {
    assert(b <= a);
    return a - b;
  }

  /**
  * @dev Adds two numbers, throws on overflow.
  */
  function add(uint256 a, uint256 b) internal pure returns (uint256) {
    uint256 c = a + b;
    assert(c >= a);
    return c;
  }
}
