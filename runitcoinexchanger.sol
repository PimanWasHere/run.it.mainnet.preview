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

  /**
   * @dev Allows the current owner to transfer control of the contract to a newOwner.
   * @param newOwner The address to transfer ownership to.
   */
  function transferOwnership(address newOwner) public onlyOwner {
    require(newOwner != address(0));
    emit OwnershipTransferred(owner, newOwner);
    owner = newOwner;
  }

  /**
   * @dev Allows the current owner to relinquish control of the contract.
   */
  function renounceOwnership() public onlyOwner {
    emit OwnershipRenounced(owner);
    owner = address(0);
  }
}



contract ERC20Basic {
  function totalSupply() public view returns (uint256);
  function balanceOf(address who) public view returns (uint256);
  function transfer(address to, uint256 value) public returns (bool);
  event Transfer(address indexed from, address indexed to, uint256 value);
}

contract BasicToken is ERC20Basic {
  using SafeMath for uint256;

  mapping(address => uint256) balances;

  uint256 totalSupply_;

  /**
  * @dev total number of tokens in existence
  */
  function totalSupply() public view returns (uint256) {
    return totalSupply_;
  }

  /**
  * @dev transfer token for a specified address
  * @param _to The address to transfer to.
  * @param _value The amount to be transferred.
  */
  function transfer(address _to, uint256 _value) public returns (bool) {
    require(_to != address(0));
    require(_value <= balances[msg.sender]);

    // SafeMath.sub will throw if there is not enough balance.
    balances[msg.sender] = balances[msg.sender].sub(_value);
    balances[_to] = balances[_to].add(_value);
    emit Transfer(msg.sender, _to, _value);
    return true;
  }

  /**
  * @dev Gets the balance of the specified address.
  * @param _owner The address to query the the balance of.
  * @return An uint256 representing the amount owned by the passed address.
  */
  function balanceOf(address _owner) public view returns (uint256 balance) {
    return balances[_owner];
  }

}

contract ERC20 is ERC20Basic {
  function allowance(address owner, address spender) public view returns (uint256);
  function transferFrom(address from, address to, uint256 value) public returns (bool);
  function approve(address spender, uint256 value) public returns (bool);
  event Approval(address indexed owner, address indexed spender, uint256 value);
}

contract StandardToken is ERC20, BasicToken {

  mapping (address => mapping (address => uint256)) internal allowed;


  /**
   * @dev Transfer tokens from one address to another
   * @param _from address The address which you want to send tokens from
   * @param _to address The address which you want to transfer to
   * @param _value  the amount of tokens to be transferred
   */
  function transferFrom(address _from, address _to, uint256 _value) public returns (bool) {
    require(_to != address(0));
    require(_value <= balances[_from]);
    require(_value <= allowed[_from][msg.sender]);

    balances[_from] = balances[_from].sub(_value);
    balances[_to] = balances[_to].add(_value);
    allowed[_from][msg.sender] = allowed[_from][msg.sender].sub(_value);
    emit Transfer(_from, _to, _value);
    return true;
  }

  /**
   * @dev Approve the passed address to spend the specified amount of tokens on behalf of msg.sender.
   *
   * Beware that changing an allowance with this method brings the risk that someone may use both the old
   * and the new allowance by unfortunate transaction ordering. One possible solution to mitigate this
   * race condition is to first reduce the spender's allowance to 0 and set the desired value afterwards:
   * https://github.com/ethereum/EIPs/issues/20#issuecomment-263524729
   * @param _spender The address which will spend the funds.
   * @param _value The amount of tokens to be spent.
   */
  function approve(address _spender, uint256 _value) public returns (bool) {
    allowed[msg.sender][_spender] = _value;
    emit Approval(msg.sender, _spender, _value);
    return true;
  }

  /**
   * @dev Function to check the amount of tokens that an owner allowed to a spender.
   * @param _owner address The address which owns the funds.
   * @param _spender address The address which will spend the funds.
   * @return A uint256 specifying the amount of tokens still available for the spender.
   */
  function allowance(address _owner, address _spender) public view returns (uint256) {
    return allowed[_owner][_spender];
  }

  /**
   * @dev Increase the amount of tokens that an owner allowed to a spender.
   *
   * approve should be called when allowed[_spender] == 0. To increment
   * allowed value is better to use this function to avoid 2 calls (and wait until
   * the first transaction is mined)
   * From MonolithDAO Token.sol
   * @param _spender The address which will spend the funds.
   * @param _addedValue The amount of tokens to increase the allowance by.
   */
  function increaseApproval(address _spender, uint _addedValue) public returns (bool) {
    allowed[msg.sender][_spender] = allowed[msg.sender][_spender].add(_addedValue);
    emit Approval(msg.sender, _spender, allowed[msg.sender][_spender]);
    return true;
  }

  /**
   * @dev Decrease the amount of tokens that an owner allowed to a spender.
   *
   * approve should be called when allowed[_spender] == 0. To decrement
   * allowed value is better to use this function to avoid 2 calls (and wait until
   * the first transaction is mined)
   * From MonolithDAO Token.sol
   * @param _spender The address which will spend the funds.
   * @param _subtractedValue The amount of tokens to decrease the allowance by.
   */
  function decreaseApproval(address _spender, uint _subtractedValue) public returns (bool) {
    uint oldValue = allowed[msg.sender][_spender];
    if (_subtractedValue > oldValue) {
      allowed[msg.sender][_spender] = 0;
    } else {
      allowed[msg.sender][_spender] = oldValue.sub(_subtractedValue);
    }
    emit Approval(msg.sender, _spender, allowed[msg.sender][_spender]);
    return true;
  }

}






contract runitcoinexchanger is Ownable {
  using SafeMath for uint256;

  // The token being sold
  ERC20 public token;

  // Address where funds are collected - the DOO Account
  address public wallet;

  // IMPORTANT pricing definition...
  // How many token units a buyer gets PER wei (tiny bar)
  uint256 public rate;

  // Amount of wei (tiny bar) raised
  uint256 public TbarRaised;

  // Testing public getters

  uint256 public tokenstobedeliveredtester;
 /*
  uint256 public currmsgvaluesentin;
  uint256 public tokenstobedeliveredtester;
  uint256 public tokensactuallydelivered;
  uint256 public hbarheldinsc;
  uint256 public hbarheldinscafterpayout;
  address public msgsenderin;
  address public beneficiaryin;
  uint256 public paidtowallet;

  uint256 public rateout;
  uint256 public tokenamountatratecalc;
  */


/**
   * @param _rate Number of RUN coins a buyer gets per HBAR, but stored in TinyBar terms ie 10*8
   * pricing ie 'rate' MUST be in WHOLE HBAR terms. ie Cannot be divisible to less than 1.
   *
   * This Contract will not be used obviously for FREE - price 0 of distributions by the DApp
   * Address where collected funds will be forwarded to.. this will be set to msg.sender ie the Deployer
   * change this if required pre-production
   * @param _token Address of the token being sold
   */
  constructor(uint256 _rate, ERC20 _token) public {
    require(_rate > 0);
    require(_token != address(0));

    rate = _rate;
    wallet = msg.sender;
    token = _token;
  }




  /**
   * Event for token purchase logging
   * @param purchaser who paid for the tokens
   * @param beneficiary who got the tokens
   * @param value in tinybars paid for purchase
   * @param amount amount of tokens purchased
   */
  event TokenPurchase(
    address indexed purchaser,
    address indexed beneficiary,
    uint256 value,
    uint256 amount
  );


  event runitpricerateUpdated(
    uint256 rate
    );


  event runitwalletUpdated(
    address wallet
    );


  // -----------------------------------------
  // Crowdsale external interface
  // -----------------------------------------

  /**
   * @dev fallback function ***DO NOT OVERRIDE*** NOT AVAILABLE in Hedera. - results in Invalid contract exception to DApp.
   */
  function () external payable {
    exchanger(msg.sender);
  }



  /**
   * @dev low level token purchase ***DO NOT OVERRIDE***
   * @param _beneficiary Address performing the token purchase
   */
  function exchanger(address _beneficiary) public payable {


    // funds received is in TINYbar ie Hbar*10**8
    // BUT rate is how many Run.it coins per HBAR.

    uint256 TbarAmount = msg.value;


    _preValidatePurchase(_beneficiary, TbarAmount);

    // calculate token amount to be created

    uint256 tokens = TbarAmount.div(rate);



    tokenstobedeliveredtester = tokens;

    // number of tokens in tinybar terms

     tokens = tokens.div(100000000);


      // add 18 dec places for token contract

     tokens = tokens.mul(1000000000000000000);


    // update state

    TbarRaised = TbarRaised.add(TbarAmount);

    _deliverTokens(_beneficiary, tokens);


    emit TokenPurchase(
      msg.sender,
      _beneficiary,
      TbarAmount,
      tokens
    );


    _forwardFunds();



  }



  function updatewallet(address _newwallet) public onlyOwner {
    require( _newwallet != address(0));
    wallet = _newwallet;

    emit runitwalletUpdated(
      wallet
      );

  }


  function updaterunitrate(uint256 _newrate) public onlyOwner {
    require(_newrate > 0);
    rate = _newrate;

    // in how many Run.it Coins to do you get for 1Hbar

    emit runitpricerateUpdated(
      rate
      );

  }

  // -----------------------------------------
  // Internal interface (extensible)
  // -----------------------------------------


  /**
   * @dev Validation of an incoming purchase. Use require statements to revert state when conditions are not met. Use super to concatenate validations.
   * @param _beneficiary Address performing the token purchase
   * @param _TbarAmount Value in tbar involved in the purchase
   */
  function _preValidatePurchase(
    address _beneficiary,
    uint256 _TbarAmount
  )
    internal
  {
    require(_beneficiary != address(0));
    require(_TbarAmount != 0);
  }




  /**
   * @dev Source of tokens. Override this method to modify the way in which the crowdsale ultimately gets and sends its tokens.
   * @param _beneficiary Address performing the token purchase
   * @param _tokenAmount Number of tokens to be emitted
   */
  function _deliverTokens(
    address _beneficiary,
    uint256 _tokenAmount
  )
    internal
  {
    token.transfer(_beneficiary, _tokenAmount);
  }




  /*
   * @dev Override to extend the way in which ether is converted to tokens.
   * @param _HbarAmount Value in wei(tinybar)to be converted into tokens
   * @return Number of tokens that can be purchased with the specified Hbar times 10 ** 18 for 18dec places in token contract

  function _getTokenAmount(uint256 _HbarAmount)
    internal view returns (uint256)
  {
    // in Hbar input terms.


    return tokenamount;

    // this returns the number of Coins to be deliver
  }
*/



  /*
   * @dev Determines how HBAR is stored/forwarded on purchases.
   */
  function _forwardFunds() internal {
    wallet.transfer(msg.value);
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
